{{#if loading}}
    <div class="margin">{{labels.loading}}</div>
{{else}}
    <div class="intelligence-research-workbench">
        <div class="row" style="margin:0 -8px;">
            {{!-- Panel 1: ProspectPool Research Queue --}}
            <div class="col-sm-4" style="padding:0 8px;box-sizing:border-box;">
                <div class="panel panel-default" style="margin-bottom:0;min-height:120px;">
                    <div class="panel-heading" style="padding:10px 12px;border-bottom:1px solid #e8e8e8;">
                        <strong style="font-size:13px;">{{labels.researchQueue}}</strong>
                    </div>
                    <div class="panel-body text-center" style="padding:16px 12px;">
                        {{#if hasQueue}}
                            <div style="font-size:36px;font-weight:700;line-height:1.1;margin-bottom:4px;">
                                <a href="{{researchQueue.href}}" style="color:#0B6E4F;text-decoration:none;">{{researchQueue.count}}</a>
                            </div>
                            <div class="text-muted" style="font-size:12px;">{{labels.awaitingResearch}}</div>
                        {{else}}
                            <div class="text-muted" style="padding:20px 0;">{{labels.noData}}</div>
                        {{/if}}
                    </div>
                </div>
            </div>

            {{!-- Panel 2: Lead Research Gaps --}}
            <div class="col-sm-4" style="padding:0 8px;box-sizing:border-box;">
                <div class="panel panel-default" style="margin-bottom:0;min-height:120px;">
                    <div class="panel-heading" style="padding:10px 12px;border-bottom:1px solid #e8e8e8;">
                        <strong style="font-size:13px;">{{labels.researchGaps}}</strong>
                    </div>
                    <div class="panel-body text-center" style="padding:16px 12px;">
                        {{#if hasGaps}}
                            <div style="font-size:36px;font-weight:700;line-height:1.1;margin-bottom:4px;">
                                <a href="{{researchGaps.href}}" style="color:#B9770E;text-decoration:none;">{{researchGaps.count}}</a>
                            </div>
                            <div class="text-muted" style="font-size:12px;">{{labels.missingEvidence}}</div>
                        {{else}}
                            <div class="text-muted" style="padding:20px 0;">{{labels.noData}}</div>
                        {{/if}}
                    </div>
                </div>
            </div>

            {{!-- Panel 3: Recent Evidence --}}
            <div class="col-sm-4" style="padding:0 8px;box-sizing:border-box;">
                <div class="panel panel-default" style="margin-bottom:0;min-height:120px;">
                    <div class="panel-heading" style="padding:10px 12px;border-bottom:1px solid #e8e8e8;">
                        <strong style="font-size:13px;">{{labels.evidencePanel}}</strong>
                    </div>
                    <div class="panel-body" style="padding:8px 12px;">
                        {{#if hasEvidence}}
                            {{#each recentEvidence}}
                                <div style="padding:4px 0;border-bottom:1px solid #f0f0f0;font-size:12px;">
                                    <a href="{{href}}" style="color:#333;text-decoration:none;">{{name}}</a>
                                    <span class="text-muted" style="margin-left:6px;">{{evidenceType}}</span>
                                </div>
                            {{/each}}
                        {{else}}
                            <div class="text-muted text-center" style="padding:20px 0;">{{labels.noItems}}</div>
                        {{/if}}
                    </div>
                </div>
            </div>
        </div>
    </div>
{{/if}}
