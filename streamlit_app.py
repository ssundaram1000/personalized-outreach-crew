import streamlit as st
from pathlib import Path

import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ModuleNotFoundError:
    # We're on macOS (no wheel) or the wheel failed to install.
    # Either fall back to the real sqlite3, or leave your stub in place.
    pass

# make src/ importable
sys.path.append(str(Path(__file__).parent / "src"))

from sales_personalized_email.crew import SalesPersonalizedEmailCrew


st.title("🎯 Prospect Outreach Drafts (CrewAI)")

# In below fields - add value = "<value for the field>" for each item - during dev only
fields = {
    "name":          st.text_input("Prospect name"),
    "title":         st.text_input("Prospect title"),
    "company":       st.text_input("Company"),
    "industry":      st.text_input("Industry"),
    "linkedin_url":  st.text_input("LinkedIn URL"),
    "our_product":   st.text_input("Your product / value prop"),
}

if st.button("Generate email ✉️"):
    # hide empty strings so required=True catches them
    cleaned = {k: v.strip() or None for k, v in fields.items()}
    missing = [k for k, v in cleaned.items() if v is None and k != "industry"]

    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
    else:
        # with st.spinner("Running CrewAI…"):
        #     result = SalesPersonalizedEmailCrew().crew().kickoff(inputs=fields)
        #     st.success("Done!")
        #     st.markdown("### ✍️ Draft email")
        #     st.write("👉 CrewOutput keys:", list(result.keys()))
        #     # st.markdown(result["write_email_task"])
        with st.spinner("Running Crew…"):
            crew_output = SalesPersonalizedEmailCrew().crew().kickoff(inputs=cleaned)

        # 1) Try the final structured result first
        email_struct = crew_output.pydantic or crew_output.json_dict

        # 2) If that’s None (e.g. you put output_json on an *earlier* task),
        #    walk through tasks_output and grab the one you want
        if email_struct is None:
            for t in crew_output.tasks_output:
                if t.task_id == "write_email_task":     # ← match your YAML/Python ID
                    email_struct = t.pydantic or t.json_dict or t.raw
                    break

        if email_struct is None:
            st.error("No structured email found – check task IDs and output_json settings.")
        else:
            # email_struct is either a PersonalizedEmail model or a dict with the same fields
            subject = email_struct.subject_line if hasattr(email_struct, "subject_line") else email_struct["subject_line"]
            body    = email_struct.email_body      if hasattr(email_struct, "email_body")   else email_struct["email_body"]
            follow  = email_struct.follow_up_notes if hasattr(email_struct, "follow_up_notes") else email_struct["follow_up_notes"]

            st.subheader("📧 Subject")
            st.write(subject)
            st.subheader("✍️ Email body")
            st.markdown(body)
            st.subheader("🔁 Follow-up notes")
            st.markdown(follow)

