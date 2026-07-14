Espo.define('custom:controllers/prospecting-dashboard', 'controllers/base', function (Dep) {
    return Dep.extend({
        actionIndex: function () {
            this.main('custom:views/prospecting/dashboard');
        },
    });
});
