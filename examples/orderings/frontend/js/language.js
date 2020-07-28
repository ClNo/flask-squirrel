(function(Lang) {
  let currentLanguageCode;
  const defaultLanguageCode = 'en'; // 'en' id default


  // -------- translation specification --------
  // -- note: better use https://github.com/fnando/i18n-js
  // --       (the syntax has been taken from there)


  const availableLanguages = [
    { code: 'en', menuText: 'English' },
    { code: 'de', menuText: 'Deutsch' }
  ];


  const translations = {};

  translations.en = {
    greeting: 'Hello %{name}',

    // datatables viewer translation file
    datatables_language_url: 'DatatablesTranslations/1.10.21/English.json',

    orderings: {
      title: 'Orderings',
      description: 'List of pending or finished company\'s internal orderings'
    },

    doc_upload: {
      title: 'Document Upload',
      description: 'Upload documents to a pool and archive them',
      upload_tool: 'Upload tool',
      upload_pool: 'Uploaded files pool'
    },

    documents: {
      title: 'Documents',
      description: 'Manage archived documents'
    },

    projects: {
      title: 'Projects',
      description: 'Manage projects'
    },

    suppliers: {
      title: 'Suppliers',
      description: 'Manage suppliers'
    },

    users: {
      title: 'Employees',
      description: 'Manage employees and user rights'
    },

    config: {
      title: 'Configuration',
      description: 'Change configurations',
      next_order_number: 'Next order number',
      save_button: 'Save',
      error_save: 'Error saving configuration - not authenticated (%{SERVER_ERROR})'
    },

    datatables_editor: {
      create: {
        button: 'New',
        title: 'Create %{ARTICLE} new %{TABLE_SINGLE}',
        submit: 'Create'
      },
      edit: {
        button: 'Edit',
        title: 'Change %{ARTICLE} %{TABLE_SINGLE}',
        submit: 'Update'
      },
      remove: {
        button: 'Delete',
        title: 'Delete %{ARTICLE} %{TABLE_SINGLE}',
        submit: 'Delete',
        confirm: {
          _: 'Do you want to delete %d %{TABLE_MULTI}?',
          1: 'Do you want to delete %{ARTICLE} %{TABLE_SINGLE}?'
        }
      },
      error: {
        system: 'A system error has occurred.'
      },
      multi: {
        title: 'Multiple %{TABLE_MULTI}',
        info: 'Different values selected. To set them to the same value please click here. '
              + 'Otherwise the values will remain.',
        restore: 'Revert changes',
        noMulti: 'This entry can be changed separately and does not belong to a group.'
      },
      datetime: {
        previous: 'previous',
        next: 'next',
        months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December'],
        weekdays: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
      }
    },

    error_web_to_db: 'Connection error between web server and database backend<br>'
                     + 'Error code: %{STATUS_CODE} (%{ERROR})<br>'
                     + 'Error message: %{SERVER_MESSAGE}',

    error_no_server: 'Server %{SERVER_NAME} is not reachable or application is not running.<br>'
                     + 'Error code: %{STATUS_CODE} (%{ERROR})<br>'
                     + 'Error message: %{TEXT_STATUS}'

  };


  translations.de = {
    greeting: 'Hallo %{name}',

    // datatables viewer translation file
    datatables_language_url: 'DatatablesTranslations/1.10.21/German.json',

    orderings: {
      title: 'Bestellungen',
      description: 'Liste von laufenden oder abgeschlossenen Firmen-interne Bestellungen'
    },

    doc_upload: {
      title: 'Dokumenten-Upload',
      description: 'Dokumente in Pool hochladen und archivieren',
      upload_tool: 'Upload Werkzeug',
      upload_pool: 'Hochgeladene Dateien im Pool'
    },

    documents: {
      title: 'Dokumente',
      description: 'Archivierte Dokumente verwalten'
    },

    projects: {
      title: 'Projekte',
      description: 'Projekte verwalten'
    },

    suppliers: {
      title: 'Lieferanten',
      description: 'Lieferanten verwalten'
    },

    users: {
      title: 'Mitarbeiter',
      description: 'Mitarbeiter verwalten and Benutzerrechte'
    },

    config: {
      title: 'Konfiguration',
      description: 'Konfiguration anpassen',
      next_order_number: 'Nächste Bestellnummer',
      save_button: 'Speichern',
      error_save: 'Fehler beim Speichern der Konfiguration - nicht eingeloggt (%{SERVER_ERROR})'
    },

    datatables_editor: {
      create: {
        button: 'Neu',
        title: 'Neue %{TABLE_SINGLE} erstellen',
        submit: 'Erstellen'
      },
      edit: {
        button: 'Ändern',
        title: '%{TABLE_SINGLE} ändern',
        submit: 'Ändern'
      },
      remove: {
        button: 'Löschen',
        title: '%{TABLE_SINGLE} löschen',
        submit: 'Löschen',
        confirm: {
          _: 'Willst du %d %{TABLE_MULTI} löschen?',
          1: 'Willst du %{ARTICLE} %{TABLE_SINGLE} löschen?'
        }
      },
      error: {
        system: 'Ein Systemfehler hat sich ereignet.'
      },
      multi: {
        title: 'Mehrere %{TABLE_MULTI}',
        info: 'Unterschiedliche Werte angewählt. Um sie zu auf den gleichen Wert zu setzen, klicke hier. '
              + 'Andernfalls bleiben sie auf ihrem Wert.',
        restore: 'Änderungen rückgängig',
        noMulti: 'Dieser Eintrag kann individuell verstellt werden und gehört nicht zu einer Gruppe.'
      },
      datetime: {
        previous: 'Vorher',
        next: 'Erstes',
        months: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September',
          'Oktober', 'November', 'Dezember'],
        weekdays: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
      }
    },

    error_web_to_db: 'Verbindungsproblem zwischen Webserver und Datenbank Server<br>'
                     + 'Fehlercode: %{STATUS_CODE} (%{ERROR})<br>'
                     + 'Fehlermeldung: %{SERVER_MESSAGE}',

    error_no_server: 'Server %{SERVER_NAME} ist nicht erreichbar oder Applikation läuft nicht.<br>'
                     + 'Error code: %{STATUS_CODE} (%{ERROR})<br>'
                     + 'Error message: %{TEXT_STATUS}'
  };


  Lang.initLanguage = function initLanguage() {
    currentLanguageCode = localStorage.getItem('current_language_code');
    if (!currentLanguageCode || (availableLanguages.findIndex(lang => lang.code === currentLanguageCode) === -1)) {
      currentLanguageCode = defaultLanguageCode;
    }
  };

  Lang.setCurrentLanguage = function setCurrentLanguage(newLangCode) {
    if (!newLangCode || (availableLanguages.findIndex(lang => lang.code === newLangCode) === -1)) {
      return;
    }

    currentLanguageCode = newLangCode;
    localStorage.setItem('current_language_code', newLangCode);
    console.log('New lang:', newLangCode);
  };

  Lang.getAvailableLanguages = function getAvailableLanguages() {
    return availableLanguages;
  };

  Lang.getCurrentLanguageCode = function getCurrentLanguage() {
    return currentLanguageCode;
  };


  // https://stackoverflow.com/questions/6491463/accessing-nested-javascript-objects-and-arays-by-string-path#6491621
  const resolvePath = (object, path, defaultValue) => path
    .split('.')
    .reduce((o, p) => (o ? o[p] : defaultValue), object);

  function replacePlaceholders(textSrc, varList) {
    let text = textSrc;
    let pos1 = text.indexOf('%{');
    while (pos1 >= 0) {
      let pos2 = text.indexOf('}', pos1);
      let placeholder = text.substr(pos1 + 2, (pos2 - pos1) - 2);
      if ((pos2 > 0) && (placeholder.length > 0)) {
        text = text.slice(0, pos1) + varList[placeholder] + text.slice(pos2 + 1);
      }
      pos1 = text.indexOf('%{', pos1 + 1);
    }
    return text;
  }

  function replaceObjPlaceholders(obj, varList) {
    for (const item in obj) {
      if (typeof (obj[item]) === 'object') {
        replaceObjPlaceholders(obj[item], varList);
      }
      else {
      // strings are handled differently than objects in JS
        obj[item] = replacePlaceholders(obj[item], varList);
      }
    }
  }

  // Translation function for translating into the current language
  Lang.t = function t(key, varList) {
  // Usage: Lang.t("greeting", {name: "John Doe"});
  //        Lang.t("orderings.title", undefined);

    const textObj = resolvePath(translations[currentLanguageCode], key);
    if (!textObj) {
      console.error(`No translation available for key "${key}" and language "${currentLanguageCode}"`);
      return undefined;
    }
    else if (typeof (textObj) == 'object') {
      let copiedObj = TableUtils.iterationCopy(textObj);
      for (const item in copiedObj) {
        if (typeof (copiedObj[item]) === 'object') {
          replaceObjPlaceholders(copiedObj[item], varList);
        }
        else {
        // strings are handled differently than objects in JS
          copiedObj[item] = replacePlaceholders(copiedObj[item], varList);
        }
      }
      // return the copied object
      return copiedObj;
    }
    // it's a string -> return a copy
    let text = String(textObj);
    return replacePlaceholders(text, varList);
  };
}(window.Lang = window.Lang || {}));
