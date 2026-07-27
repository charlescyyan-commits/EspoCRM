<div class="page-header" style="margin-top: 0;">
    <div class="pull-right text-muted" style="margin-top: 8px;">{{today}}</div>
    <h3 style="margin-top: 0;">{{labels.title}}</h3>
    <p class="text-muted" style="margin-bottom: 16px;">{{labels.subtitle}}</p>
</div>

{{#if loading}}
    <div class="panel panel-default">
        <div class="panel-body">
            <div class="text-muted">{{labels.loading}}</div>
        </div>
    </div>
{{else}}
    {{#if hasSections}}
        {{#each sections}}
            <div class="panel panel-default">
                <div class="panel-heading"><strong>{{title}}</strong></div>
                <div class="panel-body">
                    <div class="row">
                        {{#each cards}}
                            <div class="col-sm-6 col-md-3" style="margin-bottom: 16px;">
                                <div class="panel panel-default" style="margin-bottom: 0; min-height: 150px;">
                                    <div class="panel-body">
                                        <div class="text-muted" style="font-size: 12px; min-height: 34px;">{{label}}</div>
                                        {{#if isCount}}
                                            <div style="font-size: 30px; font-weight: 600; line-height: 1.2; margin-top: 8px;">
                                                <a href="{{href}}" style="color: inherit; text-decoration: none;">
                                                    {{#if count}}{{count}}{{else}}0{{/if}}
                                                </a>
                                            </div>
                                            {{#unless count}}
                                                <div class="text-muted" style="font-size: 11px; margin-top: 6px;">{{../../labels.noData}}</div>
                                            {{/unless}}
                                        {{/if}}
                                        {{#if isHandoff}}
                                            <div style="font-size: 18px; font-weight: 600; line-height: 1.2; margin-top: 12px;">
                                                <a href="{{href}}" style="color: inherit; text-decoration: none;">{{label}}</a>
                                            </div>
                                        {{/if}}
                                        {{#if description}}
                                            <div class="text-muted" style="font-size: 12px; margin-top: 12px;">
                                                {{description}}
                                            </div>
                                        {{/if}}
                                    </div>
                                </div>
                            </div>
                        {{/each}}
                    </div>
                </div>
            </div>
        {{/each}}
    {{else}}
        <div class="panel panel-default">
            <div class="panel-body text-muted">{{labels.emptyState}}</div>
        </div>
    {{/if}}

    {{#if hasPipeline}}
        <div class="panel panel-default">
            <div class="panel-heading"><strong>{{labels.pipelineSummary}}</strong></div>
            <div class="panel-body">
                <div class="row text-center">
                    {{#each pipeline}}
                        <div class="col-sm-15" style="width: 20%; float: left; padding: 0 6px; box-sizing: border-box;">
                            <div style="padding: 8px 4px;">
                                <div class="text-muted" style="font-size: 12px;">{{label}}</div>
                                <div style="font-size: 24px; font-weight: 600; line-height: 1.2;">
                                    <a href="{{href}}" style="color: inherit; text-decoration: none;">
                                        {{count}}
                                    </a>
                                </div>
                            </div>
                        </div>
                    {{/each}}
                </div>
                <div class="clearfix"></div>
            </div>
        </div>
    {{/if}}
{{/if}}
