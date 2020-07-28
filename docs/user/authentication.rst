Authentication
==============

Read access does not require any authentication, but write access does:

.. seqdiag::

   seqdiag {
      browser  -> webserver [label = "GET /api/users"];
      browser <-- webserver [label = "GET success"];
      browser  -> webserver [label = "POST new-edit-delete /api/users"];
                  # webserver  -> database [label = "INSERT comment"];
                  # webserver <-- database;
      browser <-- webserver [label = "POST FAILED, not authent.!", color = red];
   }


Because changing some tables is not allowed without authenitcaton it will be even blocked to do so in advance.
The authentication level of each table/resource will be transferred in the beginning which helps the frontend to avoid
doing actions which will be rejected anyway.

.. seqdiag::

   seqdiag {
      browser  -> webserver [label = "GET /api/login-token, UN/PW"];
      browser <-- webserver [label = "GET success: token"];
      browser  -> webserver [label = "POST new-edit-delete /api/users, send token"];
                  # webserver  -> database [label = "INSERT comment"];
                  # webserver <-- database;
      browser <-- webserver [label = "POST succeed", color = green];
   }


GET
http://zz:om@localhost:8080/ordermanagement-api/login-token
Authorization: Basic eno6b20=
Cookie: username=zz; auth_token=eyJhbGciOiJIUzUxMiIsImlhdCI6MTU3NjcxMTQ0MywiZXhwIjoxNTc2NzEyMDQzfQ.eyJpZCI6MX0.sL1McL5Z1BdYOd6ruCgcwvpPxXwnmDcB5srackaC3O__8Gg3OXbxTt744XKL6IT6UBigg5eHD7E1pWL5oKqzpg; token_expiration=2019-12-18T23:34:03.255Z; is_auth=true


Response:
{"duration":600,"is_admin":true,"token":"eyJhbGciOiJIUzUxMiIsImlhdCI6MTU3NjcxMTQ0MywiZXhwIjoxNTc2NzEyMDQzfQ.eyJpZCI6MX0.sL1McL5Z1BdYOd6ruCgcwvpPxXwnmDcB5srackaC3O__8Gg3OXbxTt744XKL6IT6UBigg5eHD7E1pWL5oKqzpg"}

From then, the authorisation header contains th following attribute:
Authorization: Bearer eyJhbGciOiJIUzUxMiIsImlhdCI6MTU3NjcxMTQ0MywiZXhwIjoxNTc2NzEyMDQzfQ.eyJpZCI6MX0.sL1McL5Z1BdYOd6ruCgcwvpPxXwnmDcB5srackaC3O__8Gg3OXbxTt744XKL6IT6UBigg5eHD7E1pWL5oKqzpg


POST
http://localhost:8080/ordermanagement-api/employees
Authorization: Bearer eyJhbGciOiJIUzUxMiIsImlhdCI6MTU3NjcxMTQ0MywiZXhwIjoxNTc2NzEyMDQzfQ.eyJpZCI6MX0.sL1McL5Z1BdYOd6ruCgcwvpPxXwnmDcB5srackaC3O__8Gg3OXbxTt744XKL6IT6UBigg5eHD7E1pWL5oKqzpg

Form data (send):
{"Form data":{"action":"create","data[0][employees][abbr]":"FF","data[0][employees][firstname]":"Fred","data[0][employees][lastname]":"Fisch","data[0][employees][credential_hash]":"ff","data[0][employees][authentication_level]":"1","data[0][employees][state]":"active","version":"1","language":"de"}}

Reply:
{"JSON":{"status":"success","data":[{"employees":{"idemployee":3,"abbr":"FF","firstname":"Fred","lastname":"Fisch","credential_hash":"----------","authentication_level":1,"state":"active"},"DT_RowId":3,"employees_state":{"name":"active"}}],"fieldErrors":[]}}



For write access to a protected table do the following steps:
    - db_customview_spec.json: set the authentication level
    - Login
    - Get access token
    - Valid for specific time...
    - Not persistent on server restarts
    - Cookie
