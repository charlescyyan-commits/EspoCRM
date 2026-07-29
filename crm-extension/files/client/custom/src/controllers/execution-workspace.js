Espo.define(
    'custom:controllers/execution-workspace',
    'controllers/base',
    function (Dep) {
        return Dep.extend({
            actionIndex: function () {
                this.main(
                    'custom:views/prospecting/execution-workspace'
                );
            },
        });
    }
);
