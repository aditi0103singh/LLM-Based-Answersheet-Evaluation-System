# app.py
import pandas as pd
from main import process_pdf  # use your existing OCR pipeline
import os
import streamlit as st
from datetime import datetime
from utils.prn_utils import normalize_prn


from db_utils import (
    init_db,
    any_admin_exists,
    create_admin,
    validate_admin,
    list_admins,
    add_batch,
    get_batches,
    add_course,
    get_courses,
    add_subject,
    get_subjects,
    save_exam_results,
    load_exam_results,
    update_exam_student_answers,
    update_exam_student_identity,
)


# ------------------------------------------------------------------
# Initial setup
# ------------------------------------------------------------------
init_db()

if "admin_id" not in st.session_state:
    st.session_state.admin_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_superadmin" not in st.session_state:
    st.session_state.is_superadmin = False
if "ocr_results" not in st.session_state:
    # {subject_id: {"answer_key": {...}, "students": {...}}}
    st.session_state.ocr_results = {}



# ------------------------------------------------------------------
# Login & registration views
# ------------------------------------------------------------------
def show_initial_admin_creation():
    st.title("Create First Admin")
    st.info("No admin exists yet. Create the very first super admin.")

    with st.form("first_admin_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create admin")

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        elif password != password2:
            st.error("Passwords do not match.")
        else:
            if create_admin(username, password, superadmin=True):
                st.success("First admin created. Please log in from the main page.")
            else:
                st.error("Could not create admin (probably duplicate username).")


def show_login():
    st.title("Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        res = validate_admin(username, password)
        if res is None:
            st.error("Invalid username or password.")
        else:
            admin_id, is_super = res
            st.session_state.admin_id = admin_id
            st.session_state.username = username
            st.session_state.is_superadmin = is_super
            st.rerun()


# ------------------------------------------------------------------
# Logged-in pages
# ------------------------------------------------------------------
def show_admin_dashboard():
    st.header(f"Welcome, {st.session_state.username}")
    st.write("Use the menu on the left to manage admins, batches, courses, and subjects.")


def show_admin_management():
    if not st.session_state.is_superadmin:
        st.warning("Only super admins can create new admins.")
        return

    st.header("Admin Management")

    st.subheader("Existing admins")
    admins = list_admins()
    if not admins:
        st.write("No admins found.")
    else:
        for admin_id, username, is_super in admins:
            super_label = " (super)" if is_super else ""
            st.write(f"- {username}{super_label}")

    st.subheader("Create new admin")
    with st.form("new_admin_form"):
        username = st.text_input("New admin username")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        make_super = st.checkbox("Make super admin")
        submitted = st.form_submit_button("Create admin")

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        elif password != password2:
            st.error("Passwords do not match.")
        else:
            if create_admin(username, password, superadmin=make_super):
                st.success("Admin created successfully.")
            else:
                st.error("Could not create admin (maybe username already exists).")



def run_ocr_for_subject(subject_id: int, pdf_file, key_file):
    """
    Save uploaded files, run OCR on the PDF, compare with key,
    and store results in session_state. One run per subject.
    """
    #base_dir = "data/uploads"
    #os.makedirs(base_dir, exist_ok=True)

    base_dir = os.path.join(
        "data",
        "uploads",
        f"subject_{subject_id}",
        datetime.now().strftime("%Y%m%d_%H%M%S"),
    )

    os.makedirs(base_dir, exist_ok=True)

    # Save PDF and key to disk
    pdf_path = os.path.join(base_dir, f"subject_{subject_id}_answers.pdf")
    key_path = os.path.join(base_dir, f"subject_{subject_id}_key.xlsx")

    with open(pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())

    with open(key_path, "wb") as f:
        f.write(key_file.getbuffer())

    # Read key Excel: first row headers, then Qno & option
    df = pd.read_excel(key_path)
    if df.shape[1] < 2:
        st.error("Key Excel must have at least two columns (Qno, Option).")
        return

    q_col = df.columns[0]
    a_col = df.columns[1]

    key_map = {}
    for _, row in df.iterrows():
        q_val = row[q_col]
        opt_val = row[a_col]
        if pd.isna(q_val):
            continue
        try:
            q_no = int(q_val)
        except ValueError:
            continue
        opt_str = "" if pd.isna(opt_val) else str(opt_val).strip().upper()
        key_map[q_no] = opt_str

    # Run your OCR pipeline for THIS pdf only
    pages = process_pdf(pdf_path)

    # Build student-level structures
    students = {}
    total_questions = len(key_map)

    for page in pages:
        name = (page.get("name") or "").strip() or "Unknown"
        #prn = (page.get("prn") or "").strip() or "UNKNOWN"
        raw_prn = (page.get("prn") or "").strip()
        prn = normalize_prn(raw_prn)
        answers = page.get("answers", {})
        img_path = page.get("image_path")

        details = []
        score = 0

        for q_no, correct_opt in key_map.items():
            raw_ans = answers.get(q_no, "")
            ans_norm = "" if raw_ans is None else str(raw_ans).strip().upper()

            is_blank = ans_norm == ""
            is_correct = (not is_blank) and (ans_norm == correct_opt)

            if is_correct:
                score += 1

            details.append(
                {
                    "question": q_no,
                    "student_answer": ans_norm if ans_norm else "(blank)",
                    "key_answer": correct_opt,
                    "is_correct": is_correct,
                    "is_blank": is_blank,
                }
            )

        """students[prn] = {
            "name": name,
            "prn": prn,
            "score": score,
            "total": total_questions,
            "details": details,
            "image_path": img_path,
        }"""

        if prn not in students:
            students[prn] = []

        students[prn].append({
            "name": name,
            "prn": prn,
            "score": score,
            "total": total_questions,
            "details": details,
            "image_path": img_path,
        })


    # persist everything in MySQL
    exam_id = save_exam_results(subject_id, pdf_path, key_path, students)

    # reload from DB (so structure matches what load_exam_results returns)
    result = load_exam_results(subject_id)
    if result is not None:
        st.session_state.ocr_results[subject_id] = result



def show_structure_management():
    st.header("Batches → Courses → Subjects")

    # ===================== BATCHES =====================
    st.subheader("Batches")
    with st.form("batch_form"):
        batch_name = st.text_input("New batch name (e.g., Aug 2025)")
        submitted_batch = st.form_submit_button("Add batch")

    if submitted_batch:
        if not batch_name.strip():
            st.error("Batch name cannot be empty.")
        elif add_batch(batch_name.strip()):
            st.success("Batch added.")
        else:
            st.error("Could not add batch (maybe name already exists).")

    batches = get_batches()
    batch_options = {name: bid for bid, name in batches}
    selected_batch_name = st.selectbox(
        "Select batch", ["-- choose --"] + list(batch_options.keys())
    )
    selected_batch_id = batch_options.get(selected_batch_name)

    # ===================== COURSES =====================
    selected_course_id = None
    if selected_batch_id:
        st.subheader(f"Courses in {selected_batch_name}")
        with st.form("course_form"):
            course_name = st.text_input("New course name (e.g., DBDA, DAC)")
            submitted_course = st.form_submit_button("Add course")

        if submitted_course:
            if not course_name.strip():
                st.error("Course name cannot be empty.")
            elif add_course(selected_batch_id, course_name.strip()):
                st.success("Course added.")
            else:
                st.error("Could not add course.")

        courses = get_courses(selected_batch_id)
        course_options = {name: cid for cid, name in courses}
        selected_course_name = st.selectbox(
            "Select course", ["-- choose --"] + list(course_options.keys())
        )
        selected_course_id = course_options.get(selected_course_name)

    # ===================== SUBJECTS =====================
    selected_subject_id = None
    if selected_course_id:
        st.subheader(f"Subjects in {selected_course_name}")
        with st.form("subject_form"):
            subject_name = st.text_input("New subject name (e.g., Java, Python)")
            submitted_subject = st.form_submit_button("Add subject")

        if submitted_subject:
            if not subject_name.strip():
                st.error("Subject name cannot be empty.")
            elif add_subject(selected_course_id, subject_name.strip()):
                st.success("Subject added.")
            else:
                st.error("Could not add subject.")

        subjects = get_subjects(selected_course_id)
        subject_options = {name: sid for sid, name in subjects}
        selected_subject_name = st.selectbox(
            "Select subject", ["-- choose --"] + list(subject_options.keys())
        )
        selected_subject_id = subject_options.get(selected_subject_name)

    st.markdown("---")

    # ===================== OCR UPLOAD =====================
    if not selected_subject_id:
        st.info("Select a subject to upload answer PDFs and keys.")
        return

    st.subheader(f"OCR & Evaluation — {selected_subject_name}")

    with st.form("upload_form"):
        pdf_file = st.file_uploader("Upload answer-sheet PDF", type=["pdf"])
        key_file = st.file_uploader("Upload answer key (Excel)", type=["xlsx", "xls"])
        submitted_upload = st.form_submit_button("Run OCR and Evaluate")

    if submitted_upload:
        if not pdf_file or not key_file:
            st.error("Upload both PDF and Excel key.")
        else:
            run_ocr_for_subject(selected_subject_id, pdf_file, key_file)
            st.success("OCR completed.")

    # ===================== LOAD RESULTS =====================
    subject_result = st.session_state.ocr_results.get(selected_subject_id)
    if subject_result is None:
        subject_result = load_exam_results(selected_subject_id)
        if subject_result:
            st.session_state.ocr_results[selected_subject_id] = subject_result

    if not subject_result:
        st.info("No OCR results yet.")
        return

    key_map = subject_result["answer_key"]
    students = subject_result["students"]

    st.subheader("Detected students (including duplicates)")

    # ===================== STUDENTS DISPLAY =====================
    for prn, entries in students.items():
        for idx, info in enumerate(entries, start=1):
            label = (
                f"{info['name']} | PRN: {prn} | "
                f"Attempt {idx} | Score {info['score']}/{info['total']}"
            )

            with st.expander(label):
                exam_student_id = info["exam_student_id"]

                # ---------- IDENTITY EDIT ----------
                col1, col2, col3 = st.columns([3, 3, 2])
                with col1:
                    new_name = st.text_input(
                        "Student Name",
                        value=info["name"],
                        key=f"name_{exam_student_id}",
                    )
                with col2:
                    new_prn = st.text_input(
                        "PRN",
                        value=prn,
                        key=f"prn_{exam_student_id}",
                    )
                with col3:
                    if st.button("Update", key=f"upd_{exam_student_id}"):
                        update_exam_student_identity(
                            exam_student_id,
                            new_prn.strip(),
                            new_name.strip(),
                        )
                        st.success("Identity updated.")
                        st.session_state.ocr_results[selected_subject_id] = load_exam_results(
                            selected_subject_id
                        )
                        st.rerun()

                st.markdown("---")

                # ---------- IMAGE ----------
                col_img, col_ans = st.columns([3, 5])
                with col_img:
                    if info["image_path"] and os.path.exists(info["image_path"]):
                        st.image(info["image_path"], width=350)
                    else:
                        st.info("No image available")

                # ---------- ANSWERS ----------
                updated_answers = {}
                details_by_q = {d["question"]: d for d in info["details"]}

                with col_ans:
                    q_numbers = sorted(key_map.keys())
                    cols = st.columns((len(q_numbers) + 9) // 10)

                    for i, qno in enumerate(q_numbers):
                        col = cols[i // 10]
                        d = details_by_q[qno]
                        cur_val = "" if d["student_answer"] in ("", "(blank)","BLANK") else d["student_answer"]

                        with col:
                            updated_answers[qno] = (
                                st.text_input(
                                    f"Q{qno} (key {key_map[qno]})",
                                    cur_val,
                                    max_chars=1,
                                    key=f"ans_{exam_student_id}_{qno}",
                                )
                                .strip()
                                .upper()
                            )

                if st.button("Recalculate Score", key=f"recalc_{exam_student_id}"):
                    new_score = 0
                    for d in info["details"]:
                        ans = updated_answers.get(d["question"], "")
                        d["student_answer"] = ans if ans else "(blank)"
                        d["is_blank"] = ans == ""
                        d["is_correct"] = ans == d["key_answer"]
                        if d["is_correct"]:
                            new_score += 1

                    update_exam_student_answers(
                        exam_student_id, new_score, info["details"]
                    )
                    st.success(f"Updated score: {new_score}/{info['total']}")
                    st.session_state.ocr_results[selected_subject_id] = load_exam_results(
                        selected_subject_id
                    )
                    st.rerun()

def show_duplicates():
    st.header("Duplicate PRN Conflicts")

    duplicates = st.session_state.get("duplicates", {})

    if not duplicates:
        st.info("No duplicate PRNs detected so far.")
        return

    for subject_id, prn_map in duplicates.items():
        st.subheader(f"Subject ID: {subject_id}")

        for prn, entries in prn_map.items():
            st.warning(f"Duplicate PRN: {prn}")

            for idx, entry in enumerate(entries, start=1):
                with st.expander(f"Entry {idx} for PRN {prn}"):

                    if entry.get("image_path") and os.path.exists(entry["image_path"]):
                        st.image(entry["image_path"], width=300)

                    new_name = st.text_input(
                        "Correct Name",
                        value=entry.get("name", ""),
                        key=f"dup_name_{subject_id}_{prn}_{idx}",
                    )

                    new_prn = st.text_input(
                        "Correct PRN",
                        value=prn,
                        key=f"dup_prn_{subject_id}_{prn}_{idx}",
                    )

                    if st.button(
                        "Resolve Duplicate",
                        key=f"resolve_{subject_id}_{prn}_{idx}",
                    ):
                        st.success(
                            "Resolved. Go back to the subject page to see updates."
                        )


# ------------------------------------------------------------------
# Layout / Routing
# ------------------------------------------------------------------
def main():
    st.set_page_config(page_title="OMR Admin Portal", layout="wide")

    if st.session_state.admin_id is None:
        # no admin logged in
        if not any_admin_exists():
            show_initial_admin_creation()
        else:
            show_login()
        return

    # logged in
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if "menu" not in st.session_state:
        st.session_state.menu = "Dashboard"
    menu_choice = st.sidebar.radio(
        "Menu",
        ("Dashboard", "Admins", "Batches / Courses / Subjects", "Duplicates / Conflicts","Logout"),
        key = "menu",
    )

    if menu_choice == "Dashboard":
        show_admin_dashboard()
    elif menu_choice == "Admins":
        show_admin_management()
    elif menu_choice == "Batches / Courses / Subjects":
        show_structure_management()
    elif menu_choice == "Duplicates / Conflicts":
        show_duplicates()

    elif menu_choice == "Logout":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


if __name__ == "__main__":
    main()
