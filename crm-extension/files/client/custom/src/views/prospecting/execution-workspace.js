Espo.define(
    'custom:views/prospecting/execution-workspace',
    'view',
    function (Dep) {
        return Dep.extend({
            template: 'custom:prospecting/execution-workspace',

            data: function () {
                return {
                    loading: this.loading,
                    labels: this.labels,
                    cards: this.cards,
                    hasCards: this.cards.length > 0,
                    canReadLedger: this.canReadLedger,
                };
            },

            setup: function () {
                this.loading = true;
                this.labels = this.buildLabels();
                this.cards = this.buildCards();
                this.canReadLedger = this.getAcl().check(
                    'ExecutionLedger',
                    'read'
                );
                this.wait(this.loadCounts());
            },

            buildLabels: function () {
                const translate = function (key) {
                    return this.getLanguage().translate(
                        key,
                        'labels',
                        'ExecutionWorkspace'
                    );
                }.bind(this);

                return {
                    title: translate('workspaceTitle'),
                    description: translate('workspaceDescription'),
                    loading: translate('loading'),
                    empty: translate('workspaceEmpty'),
                    noData: translate('noData'),
                    ledgerTimeline: translate('ledgerTimeline'),
                    ledgerDescription: translate('ledgerDescription'),
                    failureReview: translate('failureReview'),
                };
            },

            buildCards: function () {
                const acl = this.getAcl();
                const configs = [
                    {
                        label: 'activeRuns',
                        entityType: 'ProspectRun',
                        primaryFilter: 'runsActive',
                        href: '#ProspectRun/list/primary=runsActive',
                    },
                    {
                        label: 'pendingApprovals',
                        entityType: 'ActionGate',
                        primaryFilter: 'pendingApproval',
                        href: '#ActionGate/list/primary=pendingApproval',
                    },
                    {
                        label: 'completedExecutions',
                        entityType: 'ProspectRun',
                        primaryFilter: 'runsCompleted',
                        href: '#ProspectRun/list/primary=runsCompleted',
                    },
                    {
                        label: 'failedExecutions',
                        entityType: 'ProspectRun',
                        primaryFilter: 'runsFailed',
                        href: '#ProspectRun/list/primary=runsFailed',
                    },
                ];

                return configs
                    .filter(function (card) {
                        return acl.check(card.entityType, 'read');
                    })
                    .map(function (card) {
                        return {
                            label: this.getLanguage().translate(
                                card.label,
                                'labels',
                                'ExecutionWorkspace'
                            ),
                            entityType: card.entityType,
                            primaryFilter: card.primaryFilter,
                            href: card.href,
                            count: 0,
                        };
                    }, this);
            },

            loadCounts: function () {
                const self = this;
                const countPromises = this.cards.map(
                    function (card, index) {
                        return self.countRecords(
                            card.entityType,
                            card.primaryFilter
                        ).then(function (count) {
                            self.cards[index].count = count;
                        });
                    }
                );

                return Promise.all(countPromises)
                    .then(function () {
                        self.loading = false;
                    })
                    .catch(function () {
                        self.loading = false;
                    });
            },

            countRecords: function (entityType, primaryFilter) {
                const self = this;
                if (!this.getAcl().check(entityType, 'read')) {
                    return Promise.resolve(0);
                }

                return new Promise(function (resolve) {
                    self.getCollectionFactory().create(
                        entityType,
                        function (collection) {
                            collection.maxSize = 1;
                            collection.data = collection.data || {};
                            collection.data.primaryFilter = primaryFilter;
                            collection.fetch()
                                .then(function () {
                                    resolve(
                                        typeof collection.total === 'number'
                                            ? collection.total
                                            : 0
                                    );
                                })
                                .catch(function () {
                                    resolve(0);
                                });
                        }
                    );
                });
            },
        });
    }
);
