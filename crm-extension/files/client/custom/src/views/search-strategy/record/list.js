Espo.define('custom:views/search-strategy/record/list', 'views/record/list', function (Dep) {
    return Dep.extend({
        emptyStateText: 'No search strategies configured. Create a strategy to start discovery.',

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
