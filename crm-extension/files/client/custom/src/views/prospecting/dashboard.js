Espo.define('custom:views/prospecting/dashboard', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/dashboard',

        events: {
            'click [data-action="open-search"]': 'actionOpenSearch',
        },

        data: function () {
            return {
                loading: this.loading,
                metrics: this.metrics || [],
                hasMetrics: this.hasMetrics,
                recentJobs: this.recentJobs || [],
                hasRecentJobs: this.hasRecentJobs,
                centers: this.centers || [],
            };
        },

        setup: function () {
            this.loading = true;
            this.hasMetrics = false;
            this.hasRecentJobs = false;
            this.metrics = this.buildEmptyMetrics();
            this.recentJobs = [];
            this.labels = this.buildLabels();
            this.centers = this.buildCenters();
            this.wait(this.loadDashboardData());
        },

        actionOpenSearch: function () {
            this.getRouter().navigate('ProspectingSearch', {trigger: true});
        },

        buildLabels: function () {
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'Global');
            }.bind(this);

            return {
                searchCenter: translate('C17DashboardSearchCenter'),
                researchCenter: translate('C17DashboardResearchCenter'),
                outreachCenter: translate('C17DashboardOutreachCenter'),
                quoteCenter: translate('C17DashboardQuoteCenter'),
                searchDescription: translate('C17DashboardSearchDescription'),
                researchDescription: translate('C17DashboardResearchDescription'),
                outreachDescription: translate('C17DashboardOutreachDescription'),
                quoteDescription: translate('C17DashboardQuoteDescription'),
                searchStrategies: translate('C17DashboardSearchStrategies'),
                searchJobs: translate('C17DashboardSearchJobs'),
                prospectPool: translate('C17DashboardProspectPool'),
                leads: translate('C17DashboardLeads'),
                researchEvidence: translate('C17DashboardResearchEvidence'),
                salesFeedback: translate('C17DashboardSalesFeedback'),
                learningSignals: translate('C17DashboardLearningSignals'),
                draftApprovals: translate('C17DashboardDraftApprovals'),
                sendExecutions: translate('C17DashboardSendExecutions'),
                replyEvents: translate('C17DashboardReplyEvents'),
                emailEvents: translate('C17DashboardEmailEvents'),
                quotes: translate('C17DashboardQuotes'),
                quoteApprovals: translate('C17DashboardQuoteApprovals'),
                proformaInvoices: translate('C17DashboardProformaInvoices'),
            };
        },

        buildCenters: function () {
            var acl = this.getAcl();
            var filterEntries = function (entries) {
                return entries.filter(function (entry) {
                    return !entry.scope || acl.check(entry.scope, 'read');
                });
            };
            var centers = [
                {
                    name: this.labels.searchCenter,
                    href: '#ProspectingSearch',
                    description: this.labels.searchDescription,
                    entries: filterEntries([
                        {label: this.labels.searchStrategies, href: '#SearchStrategy', scope: 'SearchStrategy'},
                        {label: this.labels.searchJobs, href: '#SearchJob', scope: 'SearchJob'},
                        {label: this.labels.prospectPool, href: '#ProspectPool', scope: 'ProspectPool'},
                    ]),
                },
                {
                    name: this.labels.researchCenter,
                    href: '#Lead',
                    description: this.labels.researchDescription,
                    entries: filterEntries([
                        {label: this.labels.leads, href: '#Lead', scope: 'Lead'},
                        {label: this.labels.researchEvidence, href: '#ResearchEvidence', scope: 'ResearchEvidence'},
                        {label: this.labels.salesFeedback, href: '#SalesFeedback', scope: 'SalesFeedback'},
                        {label: this.labels.learningSignals, href: '#LearningSignal', scope: 'LearningSignal'},
                    ]),
                },
                {
                    name: this.labels.outreachCenter,
                    href: '#DraftApproval',
                    description: this.labels.outreachDescription,
                    entries: filterEntries([
                        {label: this.labels.draftApprovals, href: '#DraftApproval', scope: 'DraftApproval'},
                        {label: this.labels.sendExecutions, href: '#SendExecution', scope: 'SendExecution'},
                        {label: this.labels.replyEvents, href: '#ReplyEvent', scope: 'ReplyEvent'},
                        {label: this.labels.emailEvents, href: '#EmailEvent', scope: 'EmailEvent'},
                    ]),
                },
                {
                    name: this.labels.quoteCenter,
                    href: '#Quote',
                    description: this.labels.quoteDescription,
                    entries: filterEntries([
                        {label: this.labels.quotes, href: '#Quote', scope: 'Quote'},
                        {label: this.labels.quoteApprovals, href: '#Approval', scope: 'Approval'},
                        {label: this.labels.proformaInvoices, href: '#ProformaInvoice', scope: 'ProformaInvoice'},
                    ]),
                },
            ];

            return centers.map(function (center) {
                center.hasEntries = center.entries.length > 0;
                return center;
            });
        },

        buildEmptyMetrics: function () {
            return [
                {key: 'total', label: 'Total Prospects', value: 0, href: '#ProspectPool'},
                {key: 'newWeek', label: 'New This Week', value: 0, href: '#ProspectPool'},
                {key: 'needResearch', label: 'Need Research', value: 0, href: '#ProspectPool/list/primary=prospectsReadyForResearch'},
                {key: 'researchDone', label: 'Research Completed', value: 0, href: '#ProspectPool'},
                {key: 'highPriority', label: 'High Priority', value: 0, href: '#SearchJob'},
            ];
        },

        loadDashboardData: function () {
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
                this.loadRecentJobs(),
            ]).then(function (results) {
                self.metrics = self.buildEmptyMetrics();
                self.metrics[0].value = results[0];
                self.metrics[1].value = results[1];
                self.metrics[2].value = results[2];
                self.metrics[3].value = results[3];
                self.metrics[4].value = results[4];
                self.hasMetrics = results.slice(0, 5).some(function (n) { return n > 0; });
                self.recentJobs = results[5] || [];
                self.hasRecentJobs = self.recentJobs.length > 0;
                self.loading = false;
            }).catch(function () {
                self.metrics = self.buildEmptyMetrics();
                self.recentJobs = [];
                self.hasMetrics = false;
                self.hasRecentJobs = false;
                self.loading = false;
            });
        },

        loadRecentJobs: function () {
            var self = this;

            if (!this.getAcl().check('SearchJob', 'read')) {
                return Promise.resolve([]);
            }

            return new Promise(function (resolve) {
                self.getCollectionFactory().create('SearchJob', function (collection) {
                    collection.maxSize = 8;
                    collection.orderBy = 'createdAt';
                    collection.order = 'desc';

                    collection.fetch()
                        .then(function () {
                            var rows = collection.models.map(function (model) {
                                return {
                                    id: model.id,
                                    name: model.get('name') || 'Untitled job',
                                    status: model.get('status') || '—',
                                    createdAt: model.get('createdAt') || '—',
                                    count: model.get('resultCount') != null ? model.get('resultCount') : 0,
                                    href: '#SearchJob/view/' + model.id,
                                };
                            });
                            resolve(rows);
                        })
                        .catch(function () {
                            resolve([]);
                        });
                });
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
