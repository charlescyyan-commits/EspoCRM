Espo.define('custom:views/prospecting/search', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/search',

        events: {
            'click [data-action="create-search-job"]': 'actionCreateSearchJob',
        },

        setup: function () {
            this.labels = this.buildLabels();
        },

        data: function () {
            return {
                labels: this.labels || {},
            };
        },

        buildLabels: function () {
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'ProspectingSearch');
            }.bind(this);

            return {
                permissionDenied: translate('permissionDenied'),
                countryKeywordRequired: translate('countryKeywordRequired'),
                created: translate('created'),
                createFailed: translate('createFailed'),
                operationalCenters: translate('operationalCenters'),
                dashboard: translate('dashboard'),
                searchCenter: translate('searchCenter'),
                searchStrategies: translate('searchStrategies'),
                searchJobs: translate('searchJobs'),
                prospectPool: translate('prospectPool'),
                centerLead: translate('centerLead'),
                centerDraftApproval: translate('centerDraftApproval'),
                centerQuote: translate('centerQuote'),
                createSearchJob: translate('createSearchJob'),
                country: translate('country'),
                keyword: translate('keyword'),
                provider: translate('provider'),
                strategy: translate('strategy'),
                optionalStrategyId: translate('optionalStrategyId'),
                resultLimit: translate('resultLimit'),
                resultLimitHelp: translate('resultLimitHelp'),
                startSearch: translate('startSearch'),
                queuedOnlyHelp: translate('queuedOnlyHelp'),
            };
        },

        actionCreateSearchJob: function () {
            if (!this.getAcl().check('SearchJob', 'create')) {
                Espo.Ui.error(this.labels.permissionDenied);
                return;
            }

            var keyword = this.$el.find('[data-name="keyword"]').val().trim();
            var country = this.$el.find('[data-name="country"]').val().trim();
            var provider = this.$el.find('[data-name="provider"]').val();
            var strategyId = this.$el.find('[data-name="strategyId"]').val().trim();
            var currentUser = this.getUser();

            if (!country || !keyword) {
                Espo.Ui.error(this.labels.countryKeywordRequired);
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
                    Espo.Ui.success(this.labels.created);
                    this.getRouter().navigate('SearchJob/view/' + model.id, {trigger: true});
                }.bind(this));
            }.bind(this)).catch(function () {
                Espo.Ui.error(this.labels.createFailed);
            });
        },
    });
});
