<div class="row">
    <div class="col-sm-3">
        <div class="panel panel-default">
            <div class="panel-heading"><strong>Prospecting</strong></div>
            <div class="list-group">
                <a class="list-group-item" href="#ProspectingDashboard"><span class="fas fa-binoculars"></span> Prospecting Operations</a>
                <a class="list-group-item active" href="#ProspectingSearch"><span class="fas fa-search"></span> Search</a>
                <a class="list-group-item" href="#SearchJob"><span class="fas fa-list"></span> Search Jobs</a>
                <a class="list-group-item" href="#ProspectPool"><span class="fas fa-layer-group"></span> Prospect Pool</a>
                <a class="list-group-item" href="#ResearchEvidence"><span class="fas fa-flask"></span> Research Evidence</a>
                <a class="list-group-item" href="#SearchStrategy"><span class="fas fa-sitemap"></span> Search Strategy</a>
            </div>
        </div>
    </div>
    <div class="col-sm-9">
        <div class="page-header"><h3>Search</h3></div>
        <div class="panel panel-default">
            <div class="panel-heading">Create Search Job</div>
            <div class="panel-body">
                <div class="row">
                    <div class="col-sm-6 form-group"><label>Country</label><input class="form-control" data-name="country" type="text" maxlength="100" placeholder="Country"></div>
                    <div class="col-sm-6 form-group"><label>Keyword</label><input class="form-control" data-name="keyword" type="text" maxlength="255" placeholder="Keyword"></div>
                </div>
                <div class="row">
                    <div class="col-sm-6 form-group"><label>Provider</label><select class="form-control" data-name="provider"><option value="APIFY">Apify</option><option value="SERPER">Serper</option></select></div>
                    <div class="col-sm-6 form-group"><label>Strategy</label><input class="form-control" data-name="strategyId" type="text" placeholder="Optional Search Strategy ID"></div>
                </div>
                <div class="row">
                    <div class="col-sm-6 form-group"><label>Result Limit</label><input class="form-control" type="number" value="25" min="1" disabled><p class="help-block">Result limits remain owned by the frozen Provider/Runtime contract.</p></div>
                </div>
                <button class="btn btn-primary" data-action="create-search-job" type="button"><span class="fas fa-plus"></span> Start Search</button>
                <p class="help-block">This UI creates a queued Search Job only. It does not start a provider, worker, queue, website research, or AI process.</p>
            </div>
        </div>
    </div>
</div>
