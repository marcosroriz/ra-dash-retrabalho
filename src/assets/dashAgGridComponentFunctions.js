window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

window.dashAgGridComponentFunctions.BulletViaStringRenderer = function (props) {
    if (!props.value) return null;

    const items = props.value.split("__SEP__");

    return React.createElement(
        "ul",
        {
            style: {
                margin: 0,
                paddingLeft: "20px",
                lineHeight: "1.5",
                whiteSpace: "normal",
            },
        },
        items.map((item, i) =>
            React.createElement("li", { key: i }, item)
        )
    );
};
