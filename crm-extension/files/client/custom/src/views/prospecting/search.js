Espo.define('custom:views/prospecting/search', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/search',

        events: {
            'click [data-action="create-search-job"]': 'actionCreateSearchJob',
        },

        actionCreateSearchJob: function () {
            if (!this.getAcl().check('SearchJob', 'create')) {
                Espo.Ui.error('You do not have permission to create Search Jobs.');
                return;
            }

            var keyword = this.$el.find('[data-name="keyword"]').val().trim();
            var country = this.$el.find('[data-name="country"]').val().trim();
            var provider = this.$el.find('[data-name="provider"]').val();
            var strategyId = this.$el.find('[data-name="strategyId"]').val().trim();
            var currentUser = this.getUser();

            if (!country || !keyword) {
                Espo.Ui.error('Country and Keyword are required to create a Search Job.');
                return;
            }

            var name = keyword ? 'Prospecting: ' + keyword : 'Prospecting Search Job';
            var attributes = {
                name: name,
                keyword: keyword || null,
                country: country || null,
                source: provider || null,
                status: 'QUEUED',
                priority: 'P2',
                assignedUserId: currentUser.id,
                assignedUserName: currentUser.get('name'),
            };

            if (strategyId) {
                attributes.strategyId = strategyId;
            }

            this.getModelFactory().create('SearchJob').then(function (model) {
                model.set(attributes);

                return model.save().then(function () {
                    Espo.Ui.success('Search Job created. No provider was started.');
                    this.getRouter().navigate('SearchJob/view/' + model.id, {trigger: true});
                }.bind(this));
            }.bind(this)).catch(function () {
                Espo.Ui.error('Unable to create Search Job. Check the required Search Job fields.');
            });
        },
    });
});
