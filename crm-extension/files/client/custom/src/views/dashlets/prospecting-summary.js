Espo.define('custom:views/dashlets/prospecting-summary', 'views/dashlets/abstract/base', function (Dep) {
    return Dep.extend({
        name: 'ProspectingSummary',
        template: 'custom:dashlets/prospecting-summary',

        data: function () {
            return {
                loading: this.loading,
                metrics: this.metrics || [],
                hasAny: this.hasAny,
                labels: this.labels || {},
            };
        },

        setup: function () {
            this.loading = true;
            this.hasAny = false;
            this.labels = this.buildLabels();
            this.metrics = this.buildEmptyMetrics();
            this.wait(this.loadMetrics());
        },

        afterRender: function () {
            // no-op; template bound via data()
        },

        actionRefresh: function () {
            this.loading = true;
            this.reRender();
            this.loadMetrics().then(function () {
                this.reRender();
            }.bind(this));
        },

        buildLabels: function () {
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'ProspectingDashboard');
            }.bind(this);

            return {
                totalProspects: translate('totalProspects'),
                newThisWeek: translate('newThisWeek'),
                needResearch: translate('needResearch'),
                researchCompleted: translate('researchCompleted'),
                highPriority: translate('highPriority'),
                loading: translate('loading'),
                noData: translate('noData'),
                noActivity: translate('noActivity'),
            };
        },

        buildEmptyMetrics: function () {
            return [
                {key: 'total', label: this.labels.totalProspects, value: 0, href: '#ProspectPool'},
                {key: 'newWeek', label: this.labels.newThisWeek, value: 0, href: '#ProspectPool'},
                {key: 'needResearch', label: this.labels.needResearch, value: 0, href: '#ProspectPool/list/primary=prospectsReadyForResearch'},
                {key: 'researchDone', label: this.labels.researchCompleted, value: 0, href: '#ProspectPool'},
                {key: 'highPriority', label: this.labels.highPriority, value: 0, href: '#SearchJob'},
            ];
        },

        loadMetrics: function () {
            var self = this;

            return Promise.all([
                this.countRecords('ProspectPool', {}),
                this.countRecords('ProspectPool', {
                    where: [{type: 'lastXDays', attribute: 'createdAt', value: '7'}],
                }),
                this.countRecords('ProspectPool', {primaryFilter: 'prospectsReadyForResearch'}),
                this.countRecords('ProspectPool', {
                    where: [{type: 'equals', attribute: 'researchStatus', value: 'COMPLETED'}],
                }),
                this.countRecords('SearchJob', {
                    where: [{type: 'equals', attribute: 'priority', value: 'P1'}],
                }),
            ]).then(function (totals) {
                self.metrics = self.buildEmptyMetrics();
                self.metrics[0].value = totals[0];
                self.metrics[1].value = totals[1];
                self.metrics[2].value = totals[2];
                self.metrics[3].value = totals[3];
                self.metrics[4].value = totals[4];
                self.hasAny = totals.some(function (n) { return n > 0; });
                self.loading = false;
            }).catch(function () {
                self.metrics = self.buildEmptyMetrics();
                self.hasAny = false;
                self.loading = false;
            });
        },

        countRecords: function (entityType, options) {
            var self = this;

            if (!this.getAcl().check(entityType, 'read')) {
                return Promise.resolve(0);
            }

            return new Promise(function (resolve) {
                self.getCollectionFactory().create(entityType, function (collection) {
                    collection.maxSize = 1;
                    collection.data = collection.data || {};

                    if (options.primaryFilter) {
                        collection.data.primaryFilter = options.primaryFilter;
                    }

                    if (options.where) {
                        collection.where = options.where;
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
    });
});
