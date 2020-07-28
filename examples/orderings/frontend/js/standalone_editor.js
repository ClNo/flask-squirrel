/*
* What is a standalone editor? This is an editor which is not connected to a table object. It directly opens an editor
* and sends a POST request on success without updating a table (but could if a callback is passed).
*/
(function(StandaloneEditor, $) {
  let editorObj;

  StandaloneEditor.open = function open(editorParam) {
    editorObj = new $.fn.dataTable.Editor({
      ajax: TableUtils.generateAjaxConfig(editorParam.tableName),
      // not connected to table:  table: "...",
      fields: StandaloneEditor.createStandaloneOptions(editorParam.apiEditorSpec, editorParam.tableName)
      // TODO:  i18n: editorLangSrc
    });

    // handle disabled editor fields (= read only)
    for (const columnInd in editorParam.apiEditorSpec['editor-fields']) {
      if (editorParam.apiEditorSpec['editor-fields'][columnInd].disabled) {
        editorObj.field(editorParam.apiEditorSpec['editor-fields'][columnInd].name).disable();
      }
    }

    editorObj.on('initCreate', editorParam.onInitCreate);
    editorObj.on('initEdit', editorParam.onInitEdit);
    editorObj.on('initRemove', editorParam.onInitRemove);
    editorObj.on('submitSuccess', editorParam.onSubmitSuccess);
    editorObj.on('submitUnsuccessful', editorParam.onSubmitUnsuccessful);
    editorObj.on('submitError', editorParam.onSubmitError);
    editorObj.on('submitClosed', editorParam.onClosed);

    editorObj.on('preSubmit', function (e, data, action) {
      if (action !== 'remove') {
        const fieldSpec = editorParam.apiEditorSpec['editor-fields'];
        for (const columnno in fieldSpec) {
          if (Object.prototype.hasOwnProperty.call(fieldSpec, columnno)) { // required by eslint guard-for-in
            const fieldName = editorParam.apiEditorSpec['editor-fields'][columnno].name;
            const notNull = editorParam.apiEditorSpec['editor-fields'][columnno]['not-null'];
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

    if (editorParam.actionType === 'create') {
      editorObj.title(editorParam.title).buttons(editorParam.buttons).create();
    }
  };


  StandaloneEditor.createStandaloneOptions = function createStandaloneOptions(apiEditorSpec, tableName) {
  // https://editor.datatables.net/examples/standalone/simple.html
  // https://editor.datatables.net/reference/field/select

    let editorFields = [];
    for (const ind in apiEditorSpec['editor-fields']) {
      if (Object.prototype.hasOwnProperty.call(apiEditorSpec['editor-fields'], ind)) {
        const fieldSpec = TableUtils.iterationCopy(apiEditorSpec['editor-fields'][ind]);
        if (fieldSpec.type === 'select') {
          // This is a selection field, now copy the options to this editor field spec. This is a bit strange but that
          // must be done for a standalone editor. If it would be connected to a datatable table it would take the
          // options from there.
          for (const optionName in apiEditorSpec.options) {
            if (Object.prototype.hasOwnProperty.call(apiEditorSpec.options, optionName)) {
              // required by eslint guard-for-in
              if (optionName === fieldSpec.name) {
                // ok found the matching option
                fieldSpec.options = apiEditorSpec.options[optionName];
                break;
              }
            }
          }
          if (!fieldSpec.options) {
            console.error(`No options found for editor field ${fieldSpec.name} in table ${tableName}`);
          }
        }
        editorFields.push(fieldSpec);
      }
    }

    return editorFields;
  };
}(window.StandaloneEditor = window.StandaloneEditor || {}, jQuery));
