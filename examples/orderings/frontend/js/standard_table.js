(function(StdTable, $) {
// Private Property
  let currentTableName;
  let currentTitle;
  let currentContainerSelector;
  // let apiResponse;
  let editor; // use a global for the submit and return data rendering in the examples
  let activeFilters;

  // Public Property
  StdTable.apiResponse = undefined;
  StdTable.translation = undefined;

  StdTable.create = function create(tableName, resourceViewSpec, containerSelector) {
    if (currentTableName !== tableName) {
      // this table has been used for something different -> reset the filter

      // TODO: load current filter selection from local storage
      if (activeFilters === undefined) {
        activeFilters = {};
      }
      if (activeFilters[tableName] === undefined) {
        activeFilters[tableName] = { predef: 'default', column: {} };
      }
      // console.log('StdTable - active filters:', activeFilters[tableName]);
    }
    currentTableName = tableName;
    currentTitle = Lang.t(`${tableName}.title`);
    currentContainerSelector = containerSelector;

    // Let's start the first request to this resource/table. Now query everything right here at the beginning:
    // - filters: the predefined filters will be used to generate filter buttons
    // - translation: field name translations will be used in the table header and editor
    // - table-fields: field definitions/specifications for the data table
    // - editor-fields: field definitions/specifications for the editor
    // - options: used to provide filter widgets ("show me all documents of project X")
    // - data: unused! but for getting the options we need to query the data
    const editorFilter = undefined;
    TableUtils.apiRequest(currentTableName, undefined /* activeFilters*/, editorFilter, true, true)
      .done(function(apiJsonResponse) {
        StdTable.apiResponse = apiJsonResponse;
        // console.log('API response standard table:', currentTableName, 'response:', StdTable.apiResponse);
        StdTable.translation = apiJsonResponse.translation;
        StdTable.apiRequestDone();
      }
      );
  };

  StdTable.apiRequestDone = function apiRequestDone() {
    TableUtils.generateContainer(currentContainerSelector, currentTitle, StdTable.apiResponse.filters,
      activeFilters[currentTableName].predef, StdTable.onFilterSelected,
      StdTable.apiResponse.options, // options: used for generating column filters
      activeFilters[currentTableName].column);

    if ($.fn.dataTable.Editor) {
      const placeHolders = {
        TABLE_SINGLE: StdTable.translation.table_single,
        TABLE_MULTI: StdTable.translation.table_multi,
        ARTICLE: StdTable.translation.article,
      };

      editor = new $.fn.dataTable.Editor({
        ajax: TableUtils.generateAjaxConfig(currentTableName),
        table: '#main-table',
        fields: StdTable.apiResponse['editor-fields'],
        i18n: Lang.t('datatables_editor', placeHolders)
      });
    }
    else {
      const innerHtml = 'DataTables Editor is not available. Get a trial version '
      + '<a href="https://editor.datatables.net/download/download?type=js">here</a>. All tables are read-only.';
      $('#main-alert').addClass('alert alert-warning').attr('role', 'alert').html(innerHtml);
    }

    // Check if one or multiple columns contain a html link. If a column does, a render function must be defined below.
    // Also take a look at the uploader.js where also a table appers!
    for (const columnno in StdTable.apiResponse['table-fields']) {
      if (Object.prototype.hasOwnProperty.call(StdTable.apiResponse['table-fields'], columnno)) {
        // this "if" is requested by the eslint rule guard-for-in

        // console.log('checking', currentTableName, 'column:', StdTable.apiResponse['table-fields'][columnno]);

        if (StdTable.apiResponse['table-fields'][columnno].link_list) {
          // eslint-disable-next-line no-unused-vars
          StdTable.apiResponse['table-fields'][columnno].render = function (data, type, row, meta) {
            // console.log('render file list:', data, type, row);
            if (!data) {
              return '';
            }

            // make a string out of an array
            let content = '';
            for (const i in data.names) {
              if (Object.prototype.hasOwnProperty.call(data.names, i)) {
                // this "if" is requested by the eslint rule guard-for-in
                content += `<a href="${data.links[i]}">${data.names[i]}</a> `;
              }
            }
            return content;
          };
        }

        if (StdTable.apiResponse['table-fields'][columnno].link) {
          // this column contains a html link; expect it under the key <orig-key>_link

          StdTable.apiResponse['table-fields'][columnno].render = function (data, type, row, meta) {
            // console.log('data:', data, 'type:', type, 'row:', row);
            // console.log('meta:', meta);
            // console.log('meta.col:', meta.col);
            // console.log('apiResponse:', apiResponse['table-fields']);
            let colTableAndName = StdTable.apiResponse['table-fields'][meta.col].data;
            let colTable = colTableAndName.split('.')[0];
            let colName = colTableAndName.split('.')[1];
            let linkKey = `${colName}_link`;
            // console.log('link key: row["', colTable, '"]["', linkKey, '"] link:', row[colTable][linkKey]);
            return `<a href="${row[colTable][linkKey]}">${data}</a>`;
          };
        }
      }
    }

    if (editor) {
      // handle disabled editor fields (= read only)
      for (const columnno in StdTable.apiResponse['editor-fields']) {
        if (Object.prototype.hasOwnProperty.call(StdTable.apiResponse['editor-fields'], columnno)) {
          // this "if" is requested by the eslint rule guard-for-in
          if (StdTable.apiResponse['editor-fields'][columnno].disabled) {
            editor.field(StdTable.apiResponse['editor-fields'][columnno].name).disable();
          }
        }
      }

      // avoid any fields which must be set ("not-null") but are not set ("null")
      editor.on('preSubmit', function (e, o, action) {
        if (action !== 'remove') {
          for (const columnno in StdTable.apiResponse['editor-fields']) {
            if (Object.prototype.hasOwnProperty.call(StdTable.apiResponse['editor-fields'], columnno)) {
              // this "if" is requested by the eslint rule guard-for-in
              const fieldName = StdTable.apiResponse['editor-fields'][columnno].name;
              const notNull = StdTable.apiResponse['editor-fields'][columnno]['not-null'];
              const editorField = this.field(fieldName);
              if (notNull && !editorField.val()) {
                editorField.error(`This field (${fieldName}) must be set`);
              }
            }
          }

          // If any error was reported, cancel the submission so it can be corrected
          if (this.inError()) {
            return false; // doc: return false to stop the form being submitted
          }
        }
        return true;
      });
    }

    let buttons = [];

    if (Auth.isTableWritable(currentTableName)) {
      buttons = [
        { extend: 'create', editor: editor },
        { extend: 'edit', editor: editor },
        { extend: 'remove', editor: editor }
      ];
    }

    buttons = buttons.concat([
      'copy', 'pdf', 'excel', 'print'
    ]);

    let ajaxCustomParam = {
      predef_filter: activeFilters[currentTableName].predef,
      column_filter: TableUtils.serializeColumnFilters(activeFilters[currentTableName].column)
    };

    $('#main-table').dataTable({
      destroy: true,
      responsive: true,
      dom: 'Bfrtip',
      ajax: TableUtils.generateAjaxConfig(currentTableName, ajaxCustomParam),
      columns: StdTable.apiResponse['table-fields'],
      select: true,
      pageLength: 100,
      buttons: buttons,
      // buttons: true,
      language: {
        url: Lang.t('datatables_language_url')
      }
    });
  };

  StdTable.onFilterSelected = function onFilterSelected(predefFilterName, columnFilterName, columnFilterValue) {
    if (predefFilterName !== undefined) {
      activeFilters[currentTableName].predef = predefFilterName;
    }
    if (columnFilterName !== undefined) {
      activeFilters[currentTableName].column[columnFilterName] = columnFilterValue;
    }
    // TODO: save current filter selection to local storage

    // console.log('StdTable - active filters:', activeFilters);
    StdTable.create(currentTableName, undefined, currentContainerSelector);
  };

  StdTable.replacePlaceholders = function replacePlaceholders(textObj) {
    if (typeof (textObj) == 'object') {
      for (const item in textObj) {
        if (typeof (textObj[item]) === 'string') {
          textObj[item] = textObj[item].replace('[TABLE_SINGLE]', StdTable.translation.table_single);
          textObj[item] = textObj[item].replace('[TABLE_MULTI]', StdTable.translation.table_multi);
          textObj[item] = textObj[item].replace('[ARTICLE]', StdTable.translation.article);
        }
        else if (typeof (textObj[item]) === 'object') {
          StdTable.replacePlaceholders(textObj[item]);
        }
      }
    }
  };
}(window.StdTable = window.StdTable || {}, jQuery));
