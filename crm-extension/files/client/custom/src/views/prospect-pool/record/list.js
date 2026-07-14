Espo.define('custom:views/prospect-pool/record/list', 'views/record/list', function (Dep) {
    return Dep.extend({
        emptyStateText: 'No prospects yet. Start a discovery search to build your prospect pool.',

        setup: function () {
            Dep.prototype.setup.call(this);
            this.listenTo(this.collection, 'sync', this.applyEmptyStateText);
        },

        afterRender: function () {
            Dep.prototype.afterRender.call(this);
            this.applyEmptyStateText();
        },

        applyEmptyStateText: function () {
            var $node = this.$el.find('.no-data');
            if ($node.length) {
                $node.text(this.emptyStateText);
            }
        },
    });
});
