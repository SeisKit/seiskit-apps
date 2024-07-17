window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default:{
        OnEachFutureEvents: function(feature, layer, context) {
            layer.bindTooltip(`${feature.properties.place} (${feature.properties.mag})`)
        },
    }
});