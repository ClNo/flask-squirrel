(function(TableUtils, $) {
  TableUtils.apiPath = '/orderings-api';
  TableUtils.apiVersion = '1';

  // Bootstrap icons, licensed under MIT
  TableUtils.filterIconInline = `
<svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-funnel" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
  <path fill-rule="evenodd" d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2zm1 .5v1.308l4.372 4.858A.5.5 0 0 1 7 8.5v5.306l2-.666V8.5a.5.5 0 0 1 .128-.334L13.5 3.308V2h-11z"/>
</svg>
`;
  TableUtils.filterIconFillInline = `
<svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-funnel-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
  <path fill-rule="evenodd" d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/>
</svg>
`;

  TableUtils.apiRequest = function apiRequest(tableName, filter, editorFilter, getData = false, getSpec = true) {
    // It's dangerous to modify the ajax request header here because this header will also be used to query the language
    // file for the editor. If this file is on a CDN remote server you run into a CORS problem; this problem only
    // occurs because the authorization header is set here for all requests but they're not all to the same server.
    // So it's easier to store all datatable components on the same server and not via CDN so you do not run into the
    // cross site CORS problem.
    //
    $.ajaxSetup({
      headers: {
        Authorization: `Bearer ${Auth.getCurrentToken()}`,
      }
    });

    return $.getJSON(`${TableUtils.apiPath}/${tableName}`, {
      get: (getData && getSpec) ? 'data_spec' : ((getData) ? 'data' : 'spec'),
      version: TableUtils.apiVersion,
      lang: Lang.getCurrentLanguageCode(),
      predef_filter: filter,
      editor_filter: editorFilter
    }
    );
  };

  TableUtils.generateAjaxConfig = function generateAjaxConfig(tableName, customAjaxConf = undefined) {
    let dataConfBase = {
      get: 'data',
      version: TableUtils.apiVersion,
      lang: Lang.getCurrentLanguageCode(),
    };
    // for eslint: needs "ecmaVersion": 9
    let dataConf = { ...dataConfBase, ...customAjaxConf }; // strange "spread operator syntax"

    let ajaxData = {
      url: `${TableUtils.apiPath}/${tableName}`,
      dataSrc: 'data',
      data: dataConf,
      headers: {
        Authorization: `Bearer ${Auth.getCurrentToken()}`,
      }
    };
    return ajaxData;
  };

  TableUtils.generateContainer = function generateContainer(containerSelector, currentTitle, predefFilterList,
    activePredefFilter, onFilterSelected,
    optionsList, activeColumnFilters) {
    // first create a toolbar with predefined filters which come with the API request in the field 'filters'
    const htmlPredefFilter = TableUtils.createPredefFilterElements(predefFilterList, activePredefFilter);

    // here we create a toolbar with the column filters automatically taken from the 'options' field
    // note: predefFilterList also contains type="column" which must be handled here (disabled column filters stored here)
    const htmlFilterOptions = TableUtils.createColumnFilterElements(predefFilterList, optionsList, activeColumnFilters);

    let html = '<div id="main-container">';
    html += '<div id="main-alert"/>';
    html += `<div class="container"><h1 id="main_title">${currentTitle}</h1></div>`;
    if (htmlPredefFilter) {
      html += '<div class="container pt-3">';
      html += `<div id="filterselector">${htmlPredefFilter}</div>`;
      html += '</div>';
    }
    if (htmlFilterOptions) {
      html += '<div class="container pt-3">';
      html += `<div id="filterselector-options" class="btn-group" role="group">${htmlFilterOptions}</div>`;
      html += '</div>';
    }
    html += '<div class="container pt-3">';
    html += '<table id="main-table" class="display compact" cellspacing="0" width="100%"></table>';
    html += '</div>';
    html += '</div>';
    $(containerSelector).replaceWith(html);

    // the events will be added using jQuery's selectors; if there are no UI elements nothing will happen
    TableUtils.addPredefFilterEvents(onFilterSelected);
    TableUtils.addColumnFilterEvents(onFilterSelected);
  };

  TableUtils.add_actions = function add_actions(selectorStr, tableFieldsSpec, editorParam, actionDefs, mainCellName, storeCallback) {
    // console.log('selectorStr', selectorStr, 'tableFieldsSpec', tableFieldsSpec)

    let mainCellIndex = null;
    for (columnno in tableFieldsSpec) {
      if (tableFieldsSpec[columnno].data === mainCellName) {
        // found the cell with the given name which is the main cell
        mainCellIndex = columnno;
        mainCellIndex += 1; // add 1 because we are inserting a column in front!
        break;
      }
    }

    if ((tableFieldsSpec.length > 0) && (tableFieldsSpec[0].className === 'select-checkbox')) {
      // delete the select column as it is not used here (it's disturbing below)
      tableFieldsSpec.splice(0, 1);
    }

    if ((tableFieldsSpec.length > 0) && (tableFieldsSpec[0].data != null)) {
      // The table field spec has not been extended yet with the editor buttons. Do it now but do it only once.

      // first handle the assignment action which is a bit more complicated
      let btnContent = '';
      btnContent += '<div class="d-inline">';
      for (const action of ['add', 'edit', 'remove']) {
        if (actionDefs[action]) {
          let spacer = '';
          if (btnContent) {
            spacer = 'margin-left:.5em;';
          }
          // btnContent += '<a href="" class="btn btn-primary d-inline editor_' + action + '" title="' + actionDefs[action].linkHint + '" style="' + spacer + '">';
          // btnContent += '<img src="' + actionDefs[action].icon + '" alt="" style="height:1em;">';
          // btnContent += '</a>'
          btnContent += `<button class="btn btn-primary d-inline editor_${action}" type="button" style="margin-left:.5em;">`;
          btnContent += `<img src="${actionDefs[action].icon}" style="height:1em;">`;
          btnContent += '</button>';
        }
      }
      btnContent += '</div>';

      // upload file table: add edit/delete column
      tableFieldsSpec.splice(0, 0, {
        data: null,
        className: 'edit-btn-cell',
        defaultContent: btnContent
        // defaultContent: '<a href="" class="editor_edit" title="Datei zuweisen und im Archiv speichern"><img src="images/action-assign.svg" alt="Datei zuweisen" style="height:2em;"></a>' +
        //                '<a href="" class="editor_remove" title="Datei im Upload löschen"><img src="images/action-delete.svg" alt="Datei löschen" style="height:2em;padding-left:.5em;"></a>'
      });
    }

    $(selectorStr).off();

    // event for editing entry
    $(selectorStr).on('click', 'button.editor_add', function (e) {
      e.preventDefault();

      let localActionDefs = actionDefs;
      let title = localActionDefs.add.title;
      selectedRow = $(this).closest('tr');
      if (mainCellIndex) {
        mainCellText = selectedRow.find(`td:eq(${mainCellIndex})`).text();
        title = title.replace('%', mainCellText);
        console.log('Calling editor/add for row', mainCellText);
      }
      storeCallback(selectedRow.attr('id'), mainCellText);

      editorParam.title = title;
      editorParam.actionType = 'create';
      editorParam.buttons = localActionDefs.add.buttonText;
      StandaloneEditor.open(editorParam);
    });

    // event for editing entry
    $(selectorStr).on('click', 'button.editor_edit', function (e) {
      e.preventDefault();

      let localEditorObj = editorObject;
      let localActionDefs = actionDefs;
      let title = localActionDefs.edit.title;
      selectedRow = $(this).closest('tr');
      if (mainCellIndex) {
        mainCellText = selectedRow.find(`td:eq(${mainCellIndex})`).text();
        title = title.replace('%', mainCellText);
        console.log('Calling editor/edit for row', mainCellText);
      }
      storeCallback(selectedRow.attr('id'), mainCellText);

      localEditorObj.edit(selectedRow, {
        title: title,
        buttons: localActionDefs.edit.buttonText
      });
    });

    // upload file table: event for deleting a file
    $(selectorStr).on('click', 'button.editor_remove', function (e) {
      e.preventDefault();

      let localEditorObj = editorObject;
      let localActionDefs = actionDefs;
      let title = localActionDefs.remove.title;
      let message = localActionDefs.remove.message;
      selectedRow = $(this).closest('tr');
      if (mainCellIndex) {
        mainCellText = selectedRow.find(`td:eq(${mainCellIndex})`).text();
        title = title.replace('%', mainCellText);
        message = message.replace('%', mainCellText);
        console.log('Calling editor/remove for row', mainCellText);
      }
      storeCallback(selectedRow.attr('id'), mainCellText);

      if (localActionDefs.remove.action) {
        localActionDefs.remove.action(localActionDefs.remove, selectedRow.attr('id'));
      }
      else {
        localEditorObj.remove(selectedRow, {
          title: title,
          message: message,
          buttons: localActionDefs.remove.buttonText
        });
      }
    });
  };


  TableUtils.createPredefFilterElements = function createPredefFilterElements(apiDefinition, currentFilter) {
    if (!apiDefinition || (apiDefinition.length == 0)) {
      return undefined;
    }

    let groupHtml = '<div id="predefFilterSelector" class="btn-group btn-group-toggle" data-toggle="buttons">';

    groupHtml += '<div class="input-group-prepend">';
    groupHtml += `<div class="input-group-text" id="btnGroupAddon">${TableUtils.filterIconFillInline}</div>`; // 'Predefined'
    groupHtml += '</div>';

    for (filterDefIdx in apiDefinition) {
      const fdef = apiDefinition[filterDefIdx];

      if (fdef.type != 'predefined') {
        continue;
      }

      let currSel = '';
      if ((fdef.default === true) && (currentFilter === 'default')) {
        currSel = 'active';
      }
      else if (fdef.name === currentFilter) {
        currSel = 'active';
      }

      let transName = fdef.name;
      if (fdef.translated_name && (fdef.translated_name.length > 0)) {
        transName = fdef.translated_name;
      }

      let html = '';
      html += `<label class="btn btn-primary ${currSel}">`;
      html += `<input type="radio" name="inputsel" id="inputsel${filterDefIdx.toString()}" autocomplete="off" value="${fdef.name}">`;
      html += transName;
      html += '</label>';

      groupHtml += html;
    }
    // console.log('$(filterSelector)', $(filterSelector).html());
    groupHtml += '</div>';

    return groupHtml;
  };

  TableUtils.addPredefFilterEvents = function addPredefFilterEvents(onFilterSelected) {
    $('#predefFilterSelector :input').change(function() {
      // console.log(this); // points to the clicked input button
      console.log($(this).attr('id'), $(this).attr('value'), $(this).is(':checked'));
      let selFilter = $(this).attr('value');
      console.log('selected filter:', selFilter);
      onFilterSelected(selFilter, undefined, undefined);
    });
  };


  TableUtils.createColumnFilterElements = function createColumnFilterElements(predefFilterList, optionsList, activeColumnFilters) {
    if (!optionsList || (optionsList.length == 0)) {
      return undefined;
    }


    let groupHtml = '';
    // for bootstrap dropdowns see https://getbootstrap.com/docs/4.0/components/dropdowns/
    groupHtml += '<div class="input-group-prepend">';
    groupHtml += `<div class="input-group-text" id="btnGroupAddon">${TableUtils.filterIconFillInline}</div>`;
    groupHtml += '</div>';

    let columnCount = 0;

    for (filterDefCol in optionsList) {
      const fdef = optionsList[filterDefCol];
      // console.log('option:', filterDefCol, fdef, ' active:', activeColumnFilters[filterDefCol]);

      // Note: predefFilterList also contains type="column" which must be handled here
      let skipColumn = false;
      for (filterDefIdx in predefFilterList) {
        const filterDef = predefFilterList[filterDefIdx];
        if (filterDef.column === filterDefCol) {
          if ((filterDef.type === 'column') && (filterDef.disable === true)) {
            skipColumn = true;
            break;
          }
        }
      }

      if (skipColumn) {
        continue;
      }
      columnCount += 1;

      transName = filterDefCol;
      let selStr = '';
      selStr += '<div class="btn-group" role="group">';
      let activeClassStr = '';
      let optionNameHtml = '';

      // now set the correct filter button text according to the active filter
      if (filterDefCol in activeColumnFilters) {
        // this column found in options is also found in the currently active column filters -> set the correct text label
        let selectedLabel;
        if (activeColumnFilters[filterDefCol] === '') {
          // empty value text means no filter; expect that the first element ist the "all"/no filter element
          selectedLabel = fdef[0].label;
        }
        else {
          for (option of fdef) {
            if (option.value && (option.value.toString() === activeColumnFilters[filterDefCol])) {
              selectedLabel = option.label;
              activeClassStr = 'active';
              break;
            }
          }
        }
        if (selectedLabel) {
          optionNameHtml += selectedLabel.replaceAll('<', '&lt;').replaceAll('>', '&gt;');
        }
        else {
          optionNameHtml += `Option ${activeColumnFilters[filterDefCol].toString()}`;
        }
      }
      else {
        // no columns filter currently set -> use the first in the list
        if (fdef[0].label) {
          optionNameHtml += TableUtils.escapeText(fdef[0].label);
        }
      }

      selStr += `<button class="btn btn-primary dropdown-toggle ${activeClassStr}" type="button" id="select-${filterDefCol}" name="select-${filterDefCol}" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">`;
      selStr += optionNameHtml;
      selStr += '</button>';
      selStr += `<div class="dropdown-menu" aria-labelledby="select-${filterDefCol}">`;
      for (option of fdef) {
        let optionLabel;
        let optionValue;
        if (option.value === null) {
          // null value text means no filter; expect that the first element ist the "all"/no filter element
          optionLabel = option.label;
          optionValue = '';
        }
        else {
          optionLabel = option.label;
          optionValue = ((typeof option.value) !== 'string') ? option.value.toString() : option.value;
        }
        optionLabel = TableUtils.escapeText(optionLabel);
        optionValue = TableUtils.escapeText(optionValue);
        selStr += `<a name="optionsel" class="dropdown-item" href="#" value="${optionValue}" option="${filterDefCol}">${optionLabel}</a>`;

        if (option.value === null) {
          // separator after no "no filter"/all option
          selStr += '<div role="separator" class="dropdown-divider"></div>';
        }
      }
      selStr += '</div>';
      selStr += '</div>';

      groupHtml += selStr;
    }

    if (columnCount === 0) {
      return undefined;
    }
    return groupHtml;
  };

  TableUtils.addColumnFilterEvents = function addColumnFilterEvents(onFilterSelected) {
    $('a[name=\'optionsel\']').off().on('click', function() {
      const option = $(this).attr('option');
      const optionValue = $(this).attr('value'); // empty text means <null> which means no filter => query all items
      console.log('selected option:', option, 'value:', optionValue, 'label:', $(this).text());
      $(`button[name='select-${option}']`).text($(this).text());
      onFilterSelected(undefined, option, optionValue);
    });
  };

  TableUtils.generateEditorFilterDefaults = function generateEditorFilterDefaults(baseApiPath, editorFilterSpec) {
    if (!editorFilterSpec) {
      return undefined;
    }

    let editorFilter = '';

    for (const filterIndex in editorFilterSpec) {
      const field = editorFilterSpec[filterIndex].field;
      if (editorFilterSpec[filterIndex].default) {
        // this is the default editor filter -> use it
        if (editorFilter.length > 0) {
          editorFilter += '|';
        }
        editorFilter += `${field}:${editorFilterSpec[filterIndex].name}`;
      }
    }
    // example output: documents.idordering:projects-running
    return editorFilter;
  };

  TableUtils.serializeColumnFilters = function serializeColumnFilters(columnFilters) {
    if (!columnFilters || (Object.keys(columnFilters).length == 0)) {
      return undefined;
    }

    let columnFilter = '';
    for (const columnName in columnFilters) {
      if (!columnFilters[columnName]) {
        continue;
      }
      if (columnFilter.length > 0) {
        columnFilter += '|';
      }
      columnFilter += `${columnName}:${columnFilters[columnName]}`;
    }

    return (columnFilter.length > 0) ? columnFilter : undefined;
  };

  // source: https://github.com/jashkenas/underscore/blob/master/underscore.js#L1320
  function isObject(obj) {
    let type = typeof obj;
    return type === 'function' || type === 'object' && !!obj;
  }

  TableUtils.iterationCopy = function iterationCopy(src) {
    let target = {};
    for (let prop in src) {
      if (src.hasOwnProperty(prop)) {
      // if the value is a nested object, recursively copy all it's properties
        if (isObject(src[prop])) {
          target[prop] = iterationCopy(src[prop]);
        }
        else {
          target[prop] = src[prop];
        }
      }
    }
    return target;
  };

  TableUtils.escapeText = function escapeText(text) {
  // replaceAll() is on the way, but not yet supported in Chromium: replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    escText = text.split('<').join('&lt;');
    return escText.split('>').join('&gt;');
  };
}(window.TableUtils = window.TableUtils || {}, jQuery));
