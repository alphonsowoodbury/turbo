# User and Organization Management Functions

def show_user_management():
    """Display user management interface"""
    st.title("User Management")
    st.markdown("*Manage team members, roles, and permissions*")

    # Action Bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown("**Manage users, roles, and team access*")

    with col2:
        view_mode = st.selectbox("View", ["List", "Cards", "Table"], key="user_view")

    with col3:
        if st.button("Refresh", help="Refresh user data", key="refresh_users"):
            st.cache_data.clear()
            st.rerun()

    with col4:
        if st.button("Invite User", type="primary"):
            st.session_state.show_invite_user = True

    # Invite User Form
    if st.session_state.get("show_invite_user", False):
        with st.expander("Invite New User", expanded=True):
            with st.form("invite_user", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    email = st.text_input("Email Address*", placeholder="user@company.com")
                    first_name = st.text_input("First Name*", placeholder="John")
                    role = st.selectbox("Role", ["Member", "Admin", "Owner", "Viewer"])

                with col2:
                    last_name = st.text_input("Last Name*", placeholder="Doe")
                    department = st.text_input("Department", placeholder="Engineering")
                    message = st.text_area("Welcome Message", height=100, placeholder="Optional welcome message")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("Send Invitation", type="primary", use_container_width=True):
                        if email and first_name and last_name:
                            st.success(f"Invitation sent to {first_name} {last_name} at {email}")
                            st.session_state.show_invite_user = False
                            st.rerun()
                        else:
                            st.error("Email, first name, and last name are required")

                with col2:
                    if st.form_submit_button("Save as Draft", use_container_width=True):
                        st.info("Draft functionality coming soon!")

                with col3:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_invite_user = False
                        st.rerun()

    # Mock user data
    mock_users = [
        {"id": "1", "name": "John Doe", "email": "john@company.com", "role": "Admin", "status": "Active", "last_login": "2024-01-15", "projects": 5},
        {"id": "2", "name": "Jane Smith", "email": "jane@company.com", "role": "Member", "status": "Active", "last_login": "2024-01-14", "projects": 3},
        {"id": "3", "name": "Bob Johnson", "email": "bob@company.com", "role": "Viewer", "status": "Inactive", "last_login": "2024-01-10", "projects": 1},
        {"id": "4", "name": "Alice Brown", "email": "alice@company.com", "role": "Owner", "status": "Active", "last_login": "2024-01-15", "projects": 8},
    ]

    # Filters
    with st.container():
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            role_options = ["All"] + list(set(u["role"] for u in mock_users))
            role_filter = st.selectbox("Filter by Role", role_options, key="user_role_filter")

        with col2:
            status_options = ["All"] + list(set(u["status"] for u in mock_users))
            status_filter = st.selectbox("Filter by Status", status_options, key="user_status_filter")

        with col3:
            search = st.text_input("Search users", placeholder="Search name, email...")

        with col4:
            sort_by = st.selectbox("Sort by", ["Name", "Role", "Last Login", "Projects"])

    # Apply filters
    filtered_users = mock_users

    if role_filter != "All":
        filtered_users = [u for u in filtered_users if u["role"] == role_filter]

    if status_filter != "All":
        filtered_users = [u for u in filtered_users if u["status"] == status_filter]

    if search:
        filtered_users = [
            u for u in filtered_users
            if search.lower() in u["name"].lower() or search.lower() in u["email"].lower()
        ]

    # Display users
    st.subheader(f"Team Members ({len(filtered_users)} of {len(mock_users)})")

    if view_mode == "List":
        for user in filtered_users:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"### {user['name']}")
                    st.markdown(f"*{user['email']}*")
                    st.markdown(f"**Role:** {user['role']} | **Projects:** {user['projects']}")

                with col2:
                    status_color = "#28a745" if user['status'] == "Active" else "#6c757d"
                    st.markdown(f"**Status**")
                    st.markdown(f'<span style="color: {status_color}; font-weight: 500;">{user["status"]}</span>', unsafe_allow_html=True)

                with col3:
                    st.markdown("**Last Login**")
                    st.markdown(user['last_login'])

                with col4:
                    if st.button("Edit", key=f"edit_user_{user['id']}", use_container_width=True):
                        st.info("Edit user functionality coming soon!")

                    if st.button("Permissions", key=f"perms_{user['id']}", use_container_width=True):
                        st.info("Permission management coming soon!")

                st.divider()

    elif view_mode == "Table":
        df = pd.DataFrame(filtered_users)
        if not df.empty:
            display_df = df[['name', 'email', 'role', 'status', 'last_login', 'projects']].copy()
            display_df.columns = ['Name', 'Email', 'Role', 'Status', 'Last Login', 'Projects']

            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )

    # Team Statistics
    st.subheader("Team Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        active_users = len([u for u in mock_users if u["status"] == "Active"])
        st.metric("Active Users", active_users)

    with col2:
        admin_users = len([u for u in mock_users if u["role"] in ["Admin", "Owner"]])
        st.metric("Admins", admin_users)

    with col3:
        avg_projects = sum(u["projects"] for u in mock_users) / len(mock_users)
        st.metric("Avg Projects/User", f"{avg_projects:.1f}")

    with col4:
        total_projects = sum(u["projects"] for u in mock_users)
        st.metric("Total Project Access", total_projects)


def show_org_management():
    """Display organization management interface"""
    st.title("Organization Management")
    st.markdown("*Manage organizational settings, structure, and policies*")

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Structure", "Policies", "Billing"])

    with tab1:
        st.subheader("Organization Overview")

        # Organization Info
        col1, col2 = st.columns(2)

        with col1:
            org_info = {
                "name": "Acme Corporation",
                "plan": "Enterprise",
                "users": 47,
                "projects": 23,
                "storage": "150 GB",
                "created": "2023-06-15"
            }

            st.markdown("### Organization Details")

            with st.form("org_details"):
                org_name = st.text_input("Organization Name", value=org_info["name"])
                org_domain = st.text_input("Domain", value="acme.com")
                org_description = st.text_area("Description", value="Leading technology company focused on innovation")

                if st.form_submit_button("Update Organization"):
                    st.success("Organization details updated!")

        with col2:
            st.markdown("### Current Plan")
            st.info(f"**{org_info['plan']} Plan**")

            st.metric("Team Members", org_info["users"], "5 this month")
            st.metric("Active Projects", org_info["projects"], "2 this month")
            st.metric("Storage Used", org_info["storage"], "12 GB this month")

            if st.button("Upgrade Plan", type="primary", use_container_width=True):
                st.info("Plan upgrade functionality coming soon!")

    with tab2:
        st.subheader("Organizational Structure")

        # Department Management
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Departments")

            departments = [
                {"name": "Engineering", "members": 25, "lead": "John Doe"},
                {"name": "Product", "members": 8, "lead": "Jane Smith"},
                {"name": "Design", "members": 6, "lead": "Bob Johnson"},
                {"name": "Sales", "members": 8, "lead": "Alice Brown"}
            ]

            for dept in departments:
                with st.container():
                    st.markdown(f"**{dept['name']}**")
                    st.markdown(f"Lead: {dept['lead']} | Members: {dept['members']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Edit", key=f"edit_dept_{dept['name']}"):
                            st.info("Department editing coming soon!")
                    with col_b:
                        if st.button("Members", key=f"members_dept_{dept['name']}"):
                            st.info("Member management coming soon!")
                    st.divider()

        with col2:
            st.markdown("### Teams & Projects")

            teams = [
                {"name": "Frontend Team", "department": "Engineering", "projects": 5},
                {"name": "Backend Team", "department": "Engineering", "projects": 8},
                {"name": "Mobile Team", "department": "Engineering", "projects": 3},
                {"name": "UX Research", "department": "Design", "projects": 2}
            ]

            for team in teams:
                with st.container():
                    st.markdown(f"**{team['name']}**")
                    st.markdown(f"Department: {team['department']} | Projects: {team['projects']}")
                    if st.button("Manage", key=f"manage_team_{team['name']}"):
                        st.info("Team management coming soon!")
                    st.divider()

    with tab3:
        st.subheader("Organizational Policies")

        # Security Policies
        st.markdown("### Security Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("Require Two-Factor Authentication", value=True)
            st.checkbox("Enforce Strong Passwords", value=True)
            st.selectbox("Session Timeout", ["30 minutes", "1 hour", "4 hours", "Never"], index=1)
            st.checkbox("Allow Guest Access", value=False)

        with col2:
            st.checkbox("Email Notifications", value=True)
            st.checkbox("Slack Integration", value=False)
            st.selectbox("Data Retention", ["1 year", "2 years", "5 years", "Forever"], index=2)
            st.checkbox("Export Restrictions", value=True)

        # Project Policies
        st.markdown("### Project Management Policies")

        col1, col2 = st.columns(2)

        with col1:
            st.selectbox("Default Project Visibility", ["Team", "Department", "Organization"], index=1)
            st.checkbox("Require Project Approval", value=False)
            st.selectbox("Issue Assignment Rules", ["Open", "Team Only", "Department Only"], index=1)

        with col2:
            st.checkbox("Time Tracking Required", value=False)
            st.selectbox("Default Issue Priority", ["Low", "Medium", "High"], index=1)
            st.checkbox("Auto-Archive Completed Projects", value=True)

        if st.button("Save Policies", type="primary"):
            st.success("Organizational policies updated!")

    with tab4:
        st.subheader("Billing & Usage")

        # Usage Overview
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Monthly Cost", "$299", "+$25")
            st.metric("Per User", "$6.34", "-$0.50")

        with col2:
            st.metric("Storage Used", "150 GB", "+12 GB")
            st.metric("API Calls", "45,000", "+5,000")

        with col3:
            st.metric("Users", "47", "+5")
            st.metric("Projects", "23", "+2")

        # Billing History
        st.markdown("### Recent Billing")

        billing_data = [
            {"date": "2024-01-01", "amount": "$299", "status": "Paid"},
            {"date": "2023-12-01", "amount": "$274", "status": "Paid"},
            {"date": "2023-11-01", "amount": "$249", "status": "Paid"},
        ]

        df_billing = pd.DataFrame(billing_data)
        st.dataframe(df_billing, use_container_width=True)

        # Payment Method
        st.markdown("### Payment Method")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Credit Card** ending in 4242")
            st.markdown("Expires 12/2025")

        with col2:
            if st.button("Update Payment Method"):
                st.info("Payment update coming soon!")
            if st.button("Download Invoices"):
                st.info("Invoice download coming soon!")