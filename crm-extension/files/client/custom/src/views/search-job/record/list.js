Espo.define('custom:views/search-job/record/list', 'views/record/list', function (Dep) {
    return Dep.extend({
        emptyStateText: 'No discovery jobs yet. Create your first search job.',

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
