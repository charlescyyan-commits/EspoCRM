Espo.define('custom:views/search-strategy/detail', 'views/detail', function (Dep) {
    return Dep.extend({
        actionGenerateJobs: function () {
            Espo.Ajax.postRequest('Prospecting/search-strategy/generate-jobs', {
                strategyId: this.model.id,
            }).then(function () {
                Espo.Ui.success('Discovery Jobs generated.');
                this.model.fetch();
            }.bind(this)).catch(function (error) {
                Espo.Ui.error(error.message || 'Unable to generate Discovery Jobs.');
            });
        },
    });
});
