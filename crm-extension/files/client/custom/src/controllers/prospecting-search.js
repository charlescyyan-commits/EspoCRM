Espo.define('custom:controllers/prospecting-search', 'controllers/base', function (Dep) {
    return Dep.extend({
        actionIndex: function () {
            this.main('custom:views/prospecting/search');
        },
    });
});
