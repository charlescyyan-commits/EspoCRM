Espo.define('custom:controllers/draft-approval', 'controllers/record', function (Dep) {
    return Dep.extend({
        // Navbar `#DraftApproval` must open the workspace.
        // Native/filtered lists remain on `#DraftApproval/list[...]`.
        //
        // Espo 10 RecordController uses class-field defaultAction = 'list', so bare
        // `#DraftApproval` dispatches actionList. Detect explicit `/list` URLs to keep
        // native list access while converting the navbar entry to the workspace.
        actionIndex: function () {
            this.main('custom:views/prospecting/outreach');
        },

        actionList: function (options) {
            options = options || {};

            if (this.isExplicitNativeListRequest(options)) {
                Dep.prototype.actionList.call(this, options);
                return;
            }

            this.main('custom:views/prospecting/outreach');
        },

        isExplicitNativeListRequest: function (options) {
            if (options.primaryFilter) {
                return true;
            }

            var hash = '';

            if (typeof window !== 'undefined' && window.location && window.location.hash) {
                hash = window.location.hash;
            }

            return /#DraftApproval\/list(?:\/|\?|$)/.test(hash);
        },
    });
});
