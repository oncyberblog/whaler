$(document).ready(function() {
    $('#example').DataTable( {
        "ajax": {
            "url": "data/reports.json",
            "dataSrc": ""
        },
        "columns": [
            { "data": "timestamp" },
            { "data": "containerName" },
            { "data": "fingerprint.Image" },
            { "data": "fingerprint.MountsSource" },
            { "data": "fingerprint.Entrypoint" },
            { "data": "fingerprint.Cmd" },
            { "data": "fingerprint.Tty" },
            { "data": "pcapReport.attackerIp" },
            { "data": "fingerprint.Env" },
            { "data": "fingerprint.hostFileChanges" }
        ],
        "order": [[ 0, "desc" ]]
    } );
} );
