<div class="page-header" style="margin-top: 0;">
    <h3 style="margin-top: 0;">{{labels.searchCenter}}</h3>
    <p class="text-muted" style="margin-bottom: 16px;">{{labels.workspaceDescription}}</p>
</div>

<div class="panel panel-default">
    <div class="panel-heading"><strong>{{labels.createSearchJob}}</strong></div>
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

{{#if loading}}
    <div class="panel panel-default">
        <div class="panel-body">
            <div class="text-muted">{{labels.loading}}</div>
        </div>
    </div>
{{else}}
    {{#if hasSurfaces}}
        <div class="panel panel-default">
            <div class="panel-heading"><strong>{{labels.acquisitionPipeline}}</strong></div>
            <div class="panel-body">
                <div class="row">
                    {{#each surfaces}}
                        <div class="col-sm-4" style="margin-bottom: 16px;">
                            <div class="panel panel-default" style="margin-bottom: 0; min-height: 140px;">
                                <div class="panel-body">
                                    <div class="text-muted" style="font-size: 12px; min-height: 34px;">{{label}}</div>
                                    <div style="font-size: 30px; font-weight: 600; line-height: 1.2; margin-top: 8px;">
                                        <a href="{{href}}" style="color: inherit; text-decoration: none;">
                                            {{#if count}}{{count}}{{else}}0{{/if}}
                                        </a>
                                    </div>
                                    {{#unless count}}
                                        <div class="text-muted" style="font-size: 11px; margin-top: 6px;">{{../labels.noData}}</div>
                                    {{/unless}}
                                    {{#if description}}
                                        <div class="text-muted" style="font-size: 12px; margin-top: 12px;">{{description}}</div>
                                    {{/if}}
                                </div>
                            </div>
                        </div>
                    {{/each}}
                </div>
            </div>
        </div>
    {{else}}
        <div class="panel panel-default">
            <div class="panel-body text-muted">{{labels.workspaceEmpty}}</div>
        </div>
    {{/if}}
{{/if}}
