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
                labels: this.labels || {},
            };
        },

        setup: function () {
            this.loading = true;
            this.hasMetrics = false;
            this.hasRecentJobs = false;
            this.labels = this.buildLabels();
            this.metrics = this.buildEmptyMetrics();
            this.recentJobs = [];
            this.centers = this.buildCenters();
            this.wait(this.loadDashboardData());
        },

        actionOpenSearch: function () {
            this.getRouter().navigate('ProspectingSearch', {trigger: true});
        },

        buildLabels: function () {
            var translateGlobal = function (key) {
                return this.getLanguage().translate(key, 'labels', 'Global');
            }.bind(this);
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'ProspectingDashboard');
            }.bind(this);

            return {
                searchCenter: translateGlobal('C17DashboardSearchCenter'),
                researchCenter: translateGlobal('C17DashboardResearchCenter'),
                outreachCenter: translateGlobal('C17DashboardOutreachCenter'),
                quoteCenter: translateGlobal('C17DashboardQuoteCenter'),
                searchDescription: translateGlobal('C17DashboardSearchDescription'),
                researchDescription: translateGlobal('C17DashboardResearchDescription'),
                outreachDescription: translateGlobal('C17DashboardOutreachDescription'),
                quoteDescription: translateGlobal('C17DashboardQuoteDescription'),
                searchStrategies: translateGlobal('C17DashboardSearchStrategies'),
                searchJobs: translateGlobal('C17DashboardSearchJobs'),
                prospectPool: translateGlobal('C17DashboardProspectPool'),
                leads: translateGlobal('C17DashboardLeads'),
                researchEvidence: translateGlobal('C17DashboardResearchEvidence'),
                salesFeedback: translateGlobal('C17DashboardSalesFeedback'),
                learningSignals: translateGlobal('C17DashboardLearningSignals'),
                draftApprovals: translateGlobal('C17DashboardDraftApprovals'),
                sendExecutions: translateGlobal('C17DashboardSendExecutions'),
                replyEvents: translateGlobal('C17DashboardReplyEvents'),
                emailEvents: translateGlobal('C17DashboardEmailEvents'),
                quotes: translateGlobal('C17DashboardQuotes'),
                quoteApprovals: translateGlobal('C17DashboardQuoteApprovals'),
                proformaInvoices: translateGlobal('C17DashboardProformaInvoices'),
                prospecting: translate('prospecting'),
                dashboard: translate('dashboard'),
                workflow: translate('workflow'),
                workflowDiscover: translate('workflowDiscover'),
                workflowResearch: translate('workflowResearch'),
                workflowOutreach: translate('workflowOutreach'),
                workflowQuotes: translate('workflowQuotes'),
                operations: translate('operations'),
                operationsDescription: translate('operationsDescription'),
                operationalCenters: translate('operationalCenters'),
                analyticsDeferred: translate('analyticsDeferred'),
                summary: translate('summary'),
                loading: translate('loading'),
                noData: translate('noData'),
                noActivity: translate('noActivity'),
                recentActivity: translate('recentActivity'),
                viewAll: translate('viewAll'),
                name: translate('name'),
                status: translate('status'),
                created: translate('created'),
                count: translate('count'),
                noSearchJobs: translate('noSearchJobs'),
                startDiscover: translate('startDiscover'),
                openSearchStrategies: translate('openSearchStrategies'),
                totalProspects: translate('totalProspects'),
                newThisWeek: translate('newThisWeek'),
                needResearch: translate('needResearch'),
                researchCompleted: translate('researchCompleted'),
                highPriority: translate('highPriority'),
                untitledJob: translate('untitledJob'),
                notAvailable: translate('notAvailable'),
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
                {key: 'total', label: this.labels.totalProspects, value: 0, href: '#ProspectPool'},
                {key: 'newWeek', label: this.labels.newThisWeek, value: 0, href: '#ProspectPool'},
                {key: 'needResearch', label: this.labels.needResearch, value: 0, href: '#ProspectPool/list/primary=prospectsReadyForResearch'},
                {key: 'researchDone', label: this.labels.researchCompleted, value: 0, href: '#ProspectPool'},
                {key: 'highPriority', label: this.labels.highPriority, value: 0, href: '#SearchJob'},
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
                                    name: model.get('name') || self.labels.untitledJob,
                                    status: model.get('status') || self.labels.notAvailable,
                                    createdAt: model.get('createdAt') || self.labels.notAvailable,
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
