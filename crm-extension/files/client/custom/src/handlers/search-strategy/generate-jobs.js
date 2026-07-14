define(['action-handler'], (Dep) => {
    return class extends Dep {
        async process() {
            try {
                await Espo.Ajax.postRequest('Prospecting/search-strategy/generate-jobs', {
                    strategyId: this.view.model.id,
                });
                await this.view.model.fetch();
                Espo.Ui.success('Discovery Jobs generated.');
            } catch (error) {
                Espo.Ui.error(error.message || 'Unable to generate Discovery Jobs.');
            }
        }
    };
});
