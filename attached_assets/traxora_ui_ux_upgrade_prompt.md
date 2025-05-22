# 🧠 Replit GPT Prompt: TRAXORA UI/UX Overhaul

Please refactor TRAXORA's frontend to align with best-in-class dashboard UI/UX standards.

🎯 Objectives:
- Implement a unified layout with a consistent header or navigation bar.
- Introduce a visible navigation menu or buttons to return to the dashboard from any page.
- Ensure all modules (file uploader, report viewer, logs, agent outputs) share consistent styling and layout.
- Utilize `Card`, `Tabs`, or `Accordion` components where appropriate for clarity.
- Add breadcrumbs or page titles so the user always knows their location within the app.

🛠 Implementation Suggestions:
- Create a `DashboardLayout` component that all pages use.
- Include:
  - Title bar or app header (`TRAXORA GENIUS CORE`)
  - Sidebar or top navigation with links:
    - Upload Files
    - View Reports
    - Logs
    - Settings
- Ensure the file upload UI clearly reflects state (idle, uploading, success).

📈 Design Principles:
- Prioritize clarity and simplicity to avoid information overload.
- Use a logical information hierarchy, placing the most crucial data at the top, and more details as you scroll down.
- Employ graphs selectively to highlight important trends without overwhelming the user.
- Incorporate responsive design to ensure usability across devices.

This overhaul aims to enhance user experience by providing intuitive navigation and consistent design throughout the TRAXORA application.
