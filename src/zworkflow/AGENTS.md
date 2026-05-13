# Project Summary
* This is a python package
* This projects implements a set of REST APIs using fastapi library
    * The `src/zworkflow/apis` module implements REST APIs.
        * This module calls `core` module to handle workflow business logic
    * The `core` module is at `src/zworkflow/core`. It handles workflow business logic.
        * The `core` module calls `dal` module to do CRUD operations for workflow
    * The `dal` module is at `src/zworkflow/dal`, it stands for `Data Access Layer`
        * In `dal`, there are bunch of `DTO` classes and `DAO` classes.
        * `DAO` class stands for `Data Access Object`
        * `DTO` class stands for `Data Transfer Object`
* This project also host a single-page application at `src/zworkflow/webui`
    * This page is a static web page
    * It talks to workflow backend via REST APIs
        * `src/zworkflow/webui/ZWorkflowClient.js` is the client side of the REST APIs
    * This page has a side bar implemented in `src/zworkflow/webui/src/components/Sidebar.jsx`
    * Workflow view is implemented at `src/zworkflow/webui/src/components/Workflow.jsx`
