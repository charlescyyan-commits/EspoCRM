{{#if loading}}
    <div class="margin">{{labels.loading}}</div>
{{else}}
    <div class="row" style="margin:0 -5px;">
        {{#each metrics}}
            <div class="col-sm-15" style="width:20%;float:left;padding:0 5px;box-sizing:border-box;">
                <div class="panel panel-default" style="margin-bottom:0;">
                    <div class="panel-body text-center" style="padding:12px 8px;">
                        <div class="text-muted" style="font-size:12px;margin-bottom:4px;">{{label}}</div>
                        <div style="font-size:28px;font-weight:600;line-height:1.1;">
                            <a href="{{href}}" style="color:inherit;text-decoration:none;">{{value}}</a>
                        </div>
                        {{#unless value}}
                            <div class="text-muted" style="font-size:11px;margin-top:4px;">{{../labels.noData}}</div>
                        {{/unless}}
                    </div>
                </div>
            </div>
        {{/each}}
    </div>
    <div class="clearfix"></div>
    {{#unless hasAny}}
        <div class="text-muted margin-top" style="margin-top:10px;">
            {{labels.noActivity}}
        </div>
    {{/unless}}
{{/if}}
