Espo.define('custom:views/prospecting/search', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/search',

        events: {
            'click [data-action="create-search-job"]': 'actionCreateSearchJob',
        },

        setup: function () {
            this.loading = true;
            this.labels = this.buildLabels();
            this.surfaceConfigs = this.buildSurfaceConfigs();
            this.surfaces = this.materializeSurfaces();
            this.hasSurfaces = this.surfaces.length > 0;
            this.wait(this.loadSurfaceCounts());
        },

        data: function () {
            return {
                loading: this.loading,
                labels: this.labels || {},
                surfaces: this.surfaces || [],
                hasSurfaces: this.hasSurfaces,
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
                searchCenter: translate('searchCenter'),
                workspaceDescription: translate('workspaceDescription'),
                acquisitionPipeline: translate('acquisitionPipeline'),
                loading: translate('loading'),
                noData: translate('noData'),
                workspaceEmpty: translate('workspaceEmpty'),
                searchJobs: translate('searchJobs'),
                searchJobsDescription: translate('searchJobsDescription'),
                prospectPool: translate('prospectPool'),
                prospectPoolDescription: translate('prospectPoolDescription'),
                researchQueue: translate('researchQueue'),
                researchQueueDescription: translate('researchQueueDescription'),
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

        buildSurfaceConfigs: function () {
            return [
                {
                    key: 'searchJobs',
                    label: this.labels.searchJobs,
                    description: this.labels.searchJobsDescription,
                    scope: 'SearchJob',
                    entityType: 'SearchJob',
                    href: '#SearchJob',
                    count: 0,
                },
                {
                    key: 'prospectPool',
                    label: this.labels.prospectPool,
                    description: this.labels.prospectPoolDescription,
                    scope: 'ProspectPool',
                    entityType: 'ProspectPool',
                    href: '#ProspectPool',
                    count: 0,
                },
                {
                    key: 'researchQueue',
                    label: this.labels.researchQueue,
                    description: this.labels.researchQueueDescription,
                    scope: 'ProspectPool',
                    entityType: 'ProspectPool',
                    href: '#ProspectPool/list/primary=researchQueue',
                    primaryFilter: 'researchQueue',
                    count: 0,
                },
            ];
        },

        materializeSurfaces: function () {
            var acl = this.getAcl();

            return this.surfaceConfigs
                .filter(function (surface) {
                    return acl.check(surface.scope, 'read');
                })
                .map(function (surface) {
                    return Object.assign({}, surface);
                });
        },

        loadSurfaceCounts: function () {
            var self = this;
            var promises = this.surfaces.map(function (surface, index) {
                return self.countRecords(surface.entityType, surface.primaryFilter).then(function (count) {
                    self.surfaces[index].count = count;
                });
            });

            return Promise.all(promises).then(function () {
                self.hasSurfaces = self.surfaces.length > 0;
                self.loading = false;
            }).catch(function () {
                self.surfaces = self.materializeSurfaces();
                self.hasSurfaces = self.surfaces.length > 0;
                self.loading = false;
            });
        },

        countRecords: function (entityType, primaryFilter) {
            var self = this;

            if (!this.getAcl().check(entityType, 'read')) {
                return Promise.resolve(0);
            }

            return new Promise(function (resolve) {
                self.getCollectionFactory().create(entityType, function (collection) {
                    collection.maxSize = 1;
                    collection.data = collection.data || {};

                    if (primaryFilter) {
                        collection.data.primaryFilter = primaryFilter;
                    }

                    collection.fetch()
                        .then(function () {
                            var total = collection.total;
                            resolve(typeof total === 'number' && total >= 0 ? total : 0);
                        })
                        .catch(function () {
                            resolve(0);
                        });
                });
            });
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
