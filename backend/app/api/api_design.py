project_api = [
    {
        "POST /projects": "Creates a new project for the logged-in user."
    },
    {
        "GET /projects": "Lists all projects owned by the logged-in user."
    },
    {
        "GET /projects/{project_id}": "Gets one project owned by the logged-in user."
    },
    {
        "PATCH /projects/{project_id}": "Updates project metadata like name or description."
    },
    {
        "DELETE /projects/{project_id}": "Deletes a project or necessarily delete repo too."
    }
]

repositoy_apis = [
    {
        "GET /repositories": "Lists all repository snapshots owned by the logged-in user."
    },
    {
        "GET /repositories/{repository_id}": "Gets one repository snapshot owned by the logged-in user."
    },
    {
        "PATCH /repositories/{repository_id}": "Updates repository metadata like branch or source URL."
    },
    {
        "DELETE /repositories/{repository_id}": "Deletes a repository snapshot. but only if no other project is referencing it."
    }
]

pro_repo_attachement_apis = [
    {
        "GET /projects/{project_id}/repository": "Returns the repository currently attached to the project."
    },
    {
        "PUT /projects/{project_id}/repository": "Attaches an existing repository snapshot to the project."
    },
    {
        "POST /projects/{project_id}/repository/github": "Imports a GitHub repository snapshot, creates a repository row, attaches it to the project."
    },
    {
        "POST /projects/{project_id}/repository/zip": "Uploads a ZIP snapshot, creates a repository row, attaches it to the project."
    },
    {
        "DELETE /projects/{project_id}/repository": "Detaches the repository from the project by setting project.repository_id = null."
    }
]