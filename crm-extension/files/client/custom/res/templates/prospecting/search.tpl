<div class="row">
    <div class="col-sm-3">
        <div class="panel panel-default">
            <div class="panel-heading"><strong>{{labels.operationalCenters}}</strong></div>
            <div class="list-group">
                <a class="list-group-item" href="#ProspectingDashboard"><span class="fas fa-binoculars"></span> {{labels.dashboard}}</a>
                <a class="list-group-item active" href="#ProspectingSearch"><span class="fas fa-search"></span> {{labels.searchCenter}}</a>
                <a class="list-group-item" href="#SearchStrategy"><span class="fas fa-sitemap"></span> {{labels.searchStrategies}}</a>
                <a class="list-group-item" href="#SearchJob"><span class="fas fa-list"></span> {{labels.searchJobs}}</a>
                <a class="list-group-item" href="#ProspectPool"><span class="fas fa-layer-group"></span> {{labels.prospectPool}}</a>
                <a class="list-group-item" href="#Lead"><span class="fas fa-user-tag"></span> {{labels.centerLead}}</a>
                <a class="list-group-item" href="#DraftApproval"><span class="fas fa-paper-plane"></span> {{labels.centerDraftApproval}}</a>
                <a class="list-group-item" href="#Quote"><span class="fas fa-file-signature"></span> {{labels.centerQuote}}</a>
            </div>
        </div>
    </div>
    <div class="col-sm-9">
        <div class="page-header"><h3>{{labels.searchCenter}}</h3></div>
        <div class="panel panel-default">
            <div class="panel-heading">{{labels.createSearchJob}}</div>
            <div class="panel-body">
                <div class="row">
                    <div class="col-sm-6 form-group"><label>{{labels.country}}</label><input class="form-control" data-name="country" type="text" maxlength="100" placeholder="{{labels.country}}"></div>
                    <div class="col-sm-6 form-group"><label>{{labels.keyword}}</label><input class="form-control" data-name="keyword" type="text" maxlength="255" placeholder="{{labels.keyword}}"></div>
                </div>
                <div class="row">
                    <div class="col-sm-6 form-group"><label>{{labels.provider}}</label><select class="form-control" data-name="provider"><option value="APIFY">Apify</option><option value="SERPER">Serper</option></select></div>
                    <div class="col-sm-6 form-group"><label>{{labels.strategy}}</label><input class="form-control" data-name="strategyId" type="text" placeholder="{{labels.optionalStrategyId}}"></div>
                </div>
                <div class="row">
                    <div class="col-sm-6 form-group"><label>{{labels.resultLimit}}</label><input class="form-control" type="number" value="25" min="1" disabled><p class="help-block">{{labels.resultLimitHelp}}</p></div>
                </div>
                <button class="btn btn-primary" data-action="create-search-job" type="button"><span class="fas fa-plus"></span> {{labels.startSearch}}</button>
                <p class="help-block">{{labels.queuedOnlyHelp}}</p>
            </div>
        </div>
    </div>
</div>
