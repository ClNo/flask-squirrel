(function(Auth) {
  let currentUserName;
  let currentToken;
  let tokenExpiration;
  let userIsAdmin;

  Auth.everyoneWritableTables = [];
  Auth.adminWritableTables = [];

  Auth.initUser = function initUser() {
    // https://github.com/js-cookie/js-cookie/tree/v2.2.1

    // note: each variable could be undefined
    currentUserName = localStorage.getItem('username');
    currentToken = localStorage.getItem('auth_token');
    if (currentToken === 'undefined') { // if the "undefined" value has been stored as a string...
      currentToken = undefined;
    }
    tokenExpiration = new Date(localStorage.getItem('token_expiration'));
    userIsAdmin = localStorage.getItem('is_admin');
  };

  Auth.logSessionState = function logSessionState() {
    if (Auth.isLoggedIn()) {
      console.log('Logged in with user:', currentUserName, ' expiration time:', tokenExpiration);
    }
    else {
      console.log('NOT logged in. Last user:', currentUserName, ' last expiration time:', tokenExpiration);
    }
  };

  Auth.loggedIn = function loggedIn(username, expirationTime, token, isAdmin) {
    currentUserName = username;
    currentToken = token;
    tokenExpiration = expirationTime;
    userIsAdmin = isAdmin;
    Auth.saveCurrentUser();
  };

  Auth.logOut = function logOut() {
    currentToken = undefined;
    Auth.saveCurrentUser();
  };

  Auth.saveCurrentUser = function saveCurrentUser() {
    localStorage.setItem('username', currentUserName);
    localStorage.setItem('auth_token', currentToken);
    if (tokenExpiration) {
      localStorage.setItem('token_expiration', tokenExpiration.toISOString());
    }
    else {
      localStorage.setItem('token_expiration', undefined);
    }
    localStorage.setItem('is_admin', userIsAdmin);
  };

  Auth.isLoggedIn = function isLoggedIn() {
    if (!tokenExpiration || !currentToken) {
      return false;
    }

    const currDateTime = new Date();
    if (currDateTime.getTime() <= tokenExpiration.getTime()) {
      return true;
    }
    return false;
  };

  Auth.getLoginButtonString = function getLoginButtonString() {
    if (!Auth.isLoggedIn()) {
      return 'Login';
    }

    return `Logout ${currentUserName}`;
  };

  Auth.getCurrentToken = function getCurrentToken() {
    if (!Auth.isLoggedIn()) {
      return 'not-logged-in';
    }

    return currentToken;
  };

  Auth.isUserAdmin = function isUserAdmin() {
    if (!Auth.isLoggedIn()) {
      return false;
    }

    return userIsAdmin;
  };

  Auth.setTablesAuth = function setTablesAuth(everyoneWritableTables, adminWritableTables) {
    Auth.everyoneWritableTables = everyoneWritableTables;
    Auth.adminWritableTables = adminWritableTables;
  };

  Auth.isTableWritable = function isTableWritable(tableName) {
    if (Auth.everyoneWritableTables.includes(tableName)) {
      return true;
    }
    if (Auth.adminWritableTables.includes(tableName) && Auth.isLoggedIn() && Auth.isUserAdmin()) {
      return true;
    }
    return false;
  };
}(window.Auth = window.Auth || {}));
