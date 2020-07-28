let resourceViewSpec = {};

let authUrl = `${TableUtils.apiPath}/login-token`;
let currentView;

const navbarItems = [
  'orderings',
  'doc_upload',
  'documents',
  'projects',
  'suppliers',
  'users',
  'config'
];

function refreshCurrentView() {
  if (!currentView) {
    // do nothing if no view is currently set
    return;
  }

  if (currentView === 'doc_upload') {
    Uploader.create(currentView, resourceViewSpec, '#main-container');
  }
  else if (currentView === 'config') {
    Config.create('#main-container');
  }
  else {
    $('#main_title').html(resourceViewSpec[currentView].label);
    StdTable.create(currentView, resourceViewSpec, '#main-container');
  }
}

function setNavbarClickEvents() {
  $('nav li').off();
  $('nav li').on('click', 'a', function(e){ // step 1
    e.preventDefault(); // prevent default action, step2
    let url = $(this).attr('href'); // get the url, step 2
    console.log('nav click:', url);

    currentView = url;
    refreshCurrentView();
  });

  $('.btn-lang').off();
  $('.btn-lang').on('click', function(e){ // step 1
    e.preventDefault(); // prevent default action, step2
    let currentLang = $(this).attr('langCode'); // get the url, step 2
    Lang.setCurrentLanguage(currentLang);
    // TODO: the next code line must be fixed as it is a circular dependency
    // eslint-disable-next-line no-use-before-define
    createNavBar();
    refreshCurrentView();
  });
}

function createNavBar() {
  let listItems = '';

  for (const navItem of navbarItems) {
    const title = Lang.t(`${navItem}.title`);

    listItems += '<li class="nav-item">';
    listItems += `<a class="nav-link" href="${navItem}">${title}</a>`;
    listItems += '</li>';
  }

  $('#navbar-items').html(listItems);
  setNavbarClickEvents();
}

function updateLoginNavButton() {
  const oldText = $('#login-nav-button').html();
  const newText = Auth.getLoginButtonString();
  if (oldText !== newText) {
    $('#login-nav-button').html(newText);
    return true;
  }
  return false;
}

$('#login-form').submit(function(event) {
// $( '#login-submit' ).submit(function( event ) {
  let username = $('#login-username').val();
  let password = $('#login-password').val();
  console.log('login with un:', username);

  if ($.ajaxSettings.headers) {
    delete $.ajaxSettings.headers.Authorization;
  }
  let auth = btoa(`${username}:${password}`);
  $.ajax({
    type: 'GET',
    url: authUrl,
    headers: {
      Authorization: `Basic ${auth}`
    }
  })
    .done(function(data) {
      let expireDurationS = data.duration;
      let currentToken = data.token;
      let isAdmin = data.is_admin;
      let currTime = new Date();
      let expirationTime = currTime;
      expirationTime.setTime(currTime.getTime() + (expireDurationS * 1000));

      console.log('login succeed, duration [s]:', expireDurationS, 'expiration at:', expirationTime, 'token:',
        currentToken, 'admin:', isAdmin);

      Auth.loggedIn(username, expirationTime, currentToken, isAdmin);
      updateLoginNavButton();
      $('#modalLoginDiv').modal('hide');
      refreshCurrentView();
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
      console.log('login failed:', textStatus, errorThrown);
      updateLoginNavButton();
      $('#modalLoginDiv').modal('hide');
      refreshCurrentView();
    });

  event.preventDefault();
});

function loginNavButtonClicked() {
  if (Auth.isLoggedIn()) {
    $('#modalLoginDiv').modal('hide');
    $.getJSON(authUrl, { logout: true },
      function(apiResponseSource) {
        Auth.logOut();
        console.log('Logout answer:', apiResponseSource);
      }
    );
  }
  else {
    $('#modalLoginDiv').modal('show');
  }
}

function updateCheckLogin() {
  if (updateLoginNavButton()) {
    // a login state has been changed -> update the view because of the edit buttons etc.
    refreshCurrentView();
  }
}

// this is a shorthand for: $(document).ready( function () {
$(function() {
  Lang.initLanguage();
  Auth.initUser();
  Auth.logSessionState();
  updateLoginNavButton();

  setInterval(updateCheckLogin, 1000);

  $('.navbar-nav').off().on('click', function(){
    if ($('.navbar-header .navbar-toggle').css('display') !== 'none'){
      $('.navbar-header .navbar-toggle').trigger('click');
    }
  });

  $('#login-nav-button').off().on('click', loginNavButtonClicked);

  function selectFirstNavItem() {
    // const title = Lang.t(`${navbarItems[0]}.title`);
    StdTable.create(navbarItems[0], undefined, '#main-container');
  }

  $.getJSON(`${TableUtils.apiPath}/resource-view-spec`, {
    version: TableUtils.apiVersion,
    language: Lang.getCurrentLanguageCode()
  },
  function(apiResponse) {
    // {'data': view_spec, 'auth': {'everyone_write': everyone, 'admin_write': admin}}

    resourceViewSpec = apiResponse.data;
    Auth.setTablesAuth(apiResponse.auth.everyone_write, apiResponse.auth.admin_write);
    createNavBar();
    selectFirstNavItem();
  }
  ).fail(function(d, textStatus, error) {
    const statusCode = d.status;

    let html = '<div id="main-container"><div id="main-alert"/></div></div>';
    $('#main-container').replaceWith(html);

    const placeholders = { SERVER_MESSAGE: (d.responseJSON !== undefined) ? d.responseJSON.message : error,
      STATUS_CODE: String(statusCode), ERROR: error,
      SERVER_NAME: window.location.host, TEXT_STATUS: textStatus };

    let innerHtml;
    if (statusCode === 400) {
      // this occurs when the web server is running but the API forwarding to Flask does not work (uWSGI)
      innerHtml = Lang.t('error_web_to_db', placeholders);
    }
    else {
      // this only occurs if the web app is loaded from the browser cache but the server is not reachable at all
      innerHtml = Lang.t('error_no_server', placeholders);
    }

    console.error(innerHtml, d);
    $('#main-alert').addClass('alert alert-danger').attr('role', 'alert').html(innerHtml);
  });
});
