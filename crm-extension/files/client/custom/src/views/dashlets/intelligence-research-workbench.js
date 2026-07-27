Espo.define('custom:views/dashlets/intelligence-research-workbench', 'views/dashlets/abstract/base', function (Dep) {
    return Dep.extend({

        name: 'IntelligenceResearchWorkbench',

        template: 'custom:dashlets/intelligence-research-workbench',

        afterRender: function () {
            if (this.hasView('panels')) {
                this.getView('panels').setLoading();
            }
            this.loadWorkbench();
        },

        data: function () {
            return {
                title: this.getOption('title') || 'Intelligence Research Workbench',
                loading: this.loading !== false,
                researchQueue: this.researchQueue || {},
                researchGaps: this.researchGaps || {},
                recentEvidence: this.recentEvidence || [],
                hasQueue: this.hasQueue || false,
                hasGaps: this.hasGaps || false,
                hasEvidence: this.hasEvidence || false,
                labels: {
                    loading: this.translate('loading', 'labels'),
                    noData: this.translate('noData', 'labels', 'Global'),
                    researchQueue: this.translate('IntelligenceResearchQueue', 'labels', 'Global'),
                    researchGaps: this.translate('IntelligenceResearchGaps', 'labels', 'Global'),
                    evidencePanel: this.translate('IntelligenceEvidencePanel', 'labels', 'Global'),
                    viewAll: this.translate('viewAll', 'labels', 'Global'),
                    awaitingResearch: this.translate('IntelligenceAwaitingResearch', 'labels', 'Global'),
                    missingEvidence: this.translate('IntelligenceMissingEvidence', 'labels', 'Global'),
                    recentEvidenceItems: this.translate('IntelligenceRecentEvidenceItems', 'labels', 'Global'),
                    noItems: this.translate('noData'),
                },
            };
        },

        loadWorkbench: function () {
            var self = this;
            var acl = this.getAcl();
            var promises = [];

            // Panel 1: ProspectPool research queue count
            if (acl.check('ProspectPool', 'read')) {
                promises.push(this.countProspectPoolResearchQueue());
            } else {
                promises.push(Promise.resolve(null));
            }

            // Panel 2: Lead research gaps count
            if (acl.check('Lead', 'read')) {
                promises.push(this.countLeadResearchGaps());
            } else {
                promises.push(Promise.resolve(null));
            }

            // Panel 3: Recent ResearchEvidence
            if (acl.check('ResearchEvidence', 'read')) {
                promises.push(this.loadRecentEvidence());
            } else {
                promises.push(Promise.resolve(null));
            }

            Promise.all(promises).then(function (results) {
                if (results[0] !== null) {
                    self.researchQueue = {
                        count: results[0],
                        href: '#ProspectPool/list/primary=researchQueue',
                    };
                    self.hasQueue = true;
                }
                if (results[1] !== null) {
                    self.researchGaps = {
                        count: results[1],
                        href: '#Lead/list/primary=peMissingEvidence',
                    };
                    self.hasGaps = true;
                }
                if (results[2] !== null) {
                    self.recentEvidence = results[2];
                    self.hasEvidence = self.recentEvidence.length > 0;
                }
                self.loading = false;
                self.reRender();
            }).catch(function () {
                self.loading = false;
                self.reRender();
            });
        },

        countProspectPoolResearchQueue: function () {
            var self = this;
            return new Promise(function (resolve) {
                self.getCollectionFactory().create('ProspectPool', function (collection) {
                    collection.maxSize = 1;
                    collection.data = collection.data || {};
                    collection.data.primaryFilter = 'researchQueue';
                    collection.fetch()
                        .then(function () {
                            resolve(collection.total || 0);
                        })
                        .catch(function () { resolve(0); });
                });
            });
        },

        countLeadResearchGaps: function () {
            var self = this;
            return new Promise(function (resolve) {
                self.getCollectionFactory().create('Lead', function (collection) {
                    collection.maxSize = 1;
                    collection.data = collection.data || {};
                    collection.data.primaryFilter = 'peMissingEvidence';
                    collection.fetch()
                        .then(function () {
                            resolve(collection.total || 0);
                        })
                        .catch(function () { resolve(0); });
                });
            });
        },

        loadRecentEvidence: function () {
            var self = this;
            return new Promise(function (resolve) {
                self.getCollectionFactory().create('ResearchEvidence', function (collection) {
                    collection.maxSize = 5;
                    collection.orderBy = 'peCapturedAt';
                    collection.order = 'desc';

                    collection.fetch()
                        .then(function () {
                            var rows = collection.models.map(function (model) {
                                return {
                                    id: model.id,
                                    name: model.get('name'),
                                    evidenceType: model.get('peEvidenceType'),
                                    confidence: model.get('peConfidence'),
                                    capturedAt: model.get('peCapturedAt'),
                                    href: '#ResearchEvidence/view/' + model.id,
                                };
                            });
                            resolve(rows);
                        })
                        .catch(function () { resolve([]); });
                });
            });
        },

    });
});
