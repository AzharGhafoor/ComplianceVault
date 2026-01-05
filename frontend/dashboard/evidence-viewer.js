<script>
    window.viewEvidence = async function(controlCode, evidenceId) {
    try {
        const response = await fetch(`${window.location.origin}/api/evaluations/${controlCode}/evidence`);
    const evidence = await response.json();
        const file = evidence.find(e => e.id === evidenceId);
    if (!file) {
        alert('Evidence file not found');
    return;
        }
    const pathParts = file.file_path.split(/[\\\/]/);
    const orgId = pathParts[pathParts.length - 2];
    const filename = pathParts[pathParts.length - 1];
    window.open(`/uploads/${orgId}/${filename}`, '_blank');
    } catch (error) {
        console.error('Failed to view evidence:', error);
    alert('Failed to open evidence file');
    }
}
</script>
