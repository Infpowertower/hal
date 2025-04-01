// React Network Topology Visualization
const { useState, useEffect, useRef } = React;

// Main Network Topology Visualization Component
const NetworkTopology = () => {
    const [topology, setTopology] = useState({ nodes: [], edges: [] });
    const [selectedItem, setSelectedItem] = useState(null);
    const [highlightedPath, setHighlightedPath] = useState(null);
    const [showStubNetworks, setShowStubNetworks] = useState(false);
    const svgRef = useRef(null);
    const simulationRef = useRef(null);
    const zoomRef = useRef(null);
    
    // Fetch topology data
    const fetchTopology = async (includeStubNetworks = false) => {
        try {
            const response = await fetch(`/api/netmap/topology/?include_stub_networks=${includeStubNetworks}`);
            const data = await response.json();
            setTopology(data);
            return data;
        } catch (error) {
            console.error('Error fetching topology:', error);
            updateInfoPanel('Error loading topology data. Please try again.');
            return null;
        }
    };
    
    // Initialize the visualization
    useEffect(() => {
        fetchTopology(showStubNetworks);
        
        // Set up button handlers
        document.getElementById('reset-view-btn').addEventListener('click', resetView);
        document.getElementById('toggle-stub-btn').addEventListener('click', toggleStubNetworks);
        
        // Set up routing form handler
        document.getElementById('routing-query-form').addEventListener('submit', handleRoutingQuery);
        
        return () => {
            document.getElementById('reset-view-btn').removeEventListener('click', resetView);
            document.getElementById('toggle-stub-btn').removeEventListener('click', toggleStubNetworks);
            document.getElementById('routing-query-form').removeEventListener('submit', handleRoutingQuery);
        };
    }, []);
    
    // Update visualization when topology changes
    useEffect(() => {
        if (topology.nodes.length > 0) {
            initializeVisualization();
        }
    }, [topology]);
    
    // Initialize D3 visualization
    const initializeVisualization = () => {
        const width = document.getElementById('topology-container').clientWidth;
        const height = document.getElementById('topology-container').clientHeight;
        
        // Clear previous visualization
        d3.select('#topology-container').selectAll('*').remove();
        
        // Create SVG container
        const svg = d3.select('#topology-container')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', [0, 0, width, height])
            .call(d3.zoom().on('zoom', (event) => {
                g.attr('transform', event.transform);
            }));
            
        svgRef.current = svg;
        
        // Add a background rect to handle zoom reset
        svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'transparent');
            
        // Create main group for zoom behavior
        const g = svg.append('g');
        
        // Create links and nodes
        const link = g.append('g')
            .selectAll('line')
            .data(topology.edges.filter(e => e.source !== e.target)) // Filter out self-loops (stub networks)
            .join('line')
            .attr('class', 'link-default')
            .attr('data-network', d => d.network)
            .on('click', (event, d) => handleLinkClick(event, d));
            
        const node = g.append('g')
            .selectAll('circle')
            .data(topology.nodes)
            .join('circle')
            .attr('class', 'node-device')
            .attr('r', 15)
            .on('click', (event, d) => handleNodeClick(event, d))
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
                
        // Add labels to nodes
        const labels = g.append('g')
            .selectAll('text')
            .data(topology.nodes)
            .join('text')
            .attr('class', 'node-label')
            .attr('dy', 30)
            .attr('text-anchor', 'middle')
            .text(d => d.label);
            
        // Set up force simulation
        const simulation = d3.forceSimulation(topology.nodes)
            .force('link', d3.forceLink(topology.edges.filter(e => e.source !== e.target))
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                    
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                    
                labels
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
            
        simulationRef.current = simulation;
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    };
    
    // Handle node click
    const handleNodeClick = async (event, node) => {
        setSelectedItem({ type: 'node', data: node });
        
        // Reset previous highlights
        d3.selectAll('.node-device').classed('node-selected', false);
        d3.selectAll('.link-default').classed('link-active', false);
        
        // Highlight selected node
        d3.select(event.currentTarget).classed('node-selected', true);
        
        try {
            // Fetch device networks
            const response = await fetch(`/api/netmap/devices/${node.id}/networks/`);
            if (!response.ok) throw new Error('Failed to fetch device networks');
            
            const data = await response.json();
            
            // Update info panel with device details
            let html = `<h5>${node.label}</h5>`;
            html += `<p><strong>Interfaces:</strong> ${node.interfaces_count}</p>`;
            html += `<p><strong>Networks:</strong></p>`;
            html += `<ul>`;
            data.forEach(network => {
                html += `<li>${network.network} (${network.interfaces.length} interfaces)</li>`;
            });
            html += `</ul>`;
            
            updateInfoPanel(html);
            
        } catch (error) {
            console.error('Error fetching device networks:', error);
            updateInfoPanel(`<p>Error fetching details for device ${node.label}</p>`);
        }
    };
    
    // Handle link click
    const handleLinkClick = async (event, link) => {
        setSelectedItem({ type: 'link', data: link });
        
        // Reset previous highlights
        d3.selectAll('.node-device').classed('node-selected', false);
        d3.selectAll('.link-default').classed('link-active', false);
        
        // Highlight selected link
        d3.select(event.currentTarget).classed('link-active', true);
        
        try {
            // Determine the source and target IDs
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            
            // Fetch connection details
            const response = await fetch(`/api/netmap/connections/?device1_id=${sourceId}&device2_id=${targetId}`);
            if (!response.ok) throw new Error('Failed to fetch connection details');
            
            const data = await response.json();
            
            // Get labels for display
            const sourceLabel = typeof link.source === 'object' ? link.source.label : link.source_label;
            const targetLabel = typeof link.target === 'object' ? link.target.label : link.target_label;
            
            // Update info panel with connection details
            let html = `<h5>Connection Details</h5>`;
            html += `<p><strong>Devices:</strong> ${sourceLabel} ↔ ${targetLabel}</p>`;
            html += `<p><strong>Network:</strong> ${link.network}</p>`;
            
            if (data.connections && data.connections.length > 0) {
                data.connections.forEach(conn => {
                    if (conn.routes_through_connection && conn.routes_through_connection.length > 0) {
                        html += `<p><strong>Routes using this connection:</strong></p>`;
                        html += `<ul>`;
                        conn.routes_through_connection.forEach(route => {
                            html += `<li>${route.source_device}: ${route.destination_network} via ${route.gateway_ip} (${route.type})</li>`;
                        });
                        html += `</ul>`;
                    } else {
                        html += `<p>No routes using this connection.</p>`;
                    }
                });
            } else {
                html += `<p>No detailed routing information available.</p>`;
            }
            
            updateInfoPanel(html);
            
        } catch (error) {
            console.error('Error fetching connection details:', error);
            const sourceLabel = typeof link.source === 'object' ? link.source.label : link.source_label;
            const targetLabel = typeof link.target === 'object' ? link.target.label : link.target_label;
            updateInfoPanel(`<p>Error fetching details for connection between ${sourceLabel} and ${targetLabel}</p>`);
        }
    };
    
    // Handle routing query
    const handleRoutingQuery = async (event) => {
        event.preventDefault();
        
        const sourceInput = document.getElementById('source-input').value;
        const destinationInput = document.getElementById('destination-input').value;
        
        if (!sourceInput || !destinationInput) {
            updateResultsPanel('<p class="text-danger">Please enter both source and destination.</p>');
            return;
        }
        
        try {
            const response = await fetch(`/api/netmap/routing-path/?source=${encodeURIComponent(sourceInput)}&destination=${encodeURIComponent(destinationInput)}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update results panel
                let html = `<p class="text-success">Path found from ${data.source} to ${data.destination}</p>`;
                html += `<ol>`;
                data.path.forEach(hop => {
                    html += `<li>${hop.device}`;
                    if (hop.note) {
                        html += ` (${hop.note})`;
                    } else if (hop.next_hop) {
                        html += ` → ${hop.next_hop}`;
                    }
                    html += `</li>`;
                });
                html += `</ol>`;
                
                if (data.nat_applied && (data.nat_applied.source || data.nat_applied.destination)) {
                    html += `<p><strong>NAT applied:</strong> `;
                    if (data.nat_applied.source) html += `Source `;
                    if (data.nat_applied.source && data.nat_applied.destination) html += `and `;
                    if (data.nat_applied.destination) html += `Destination`;
                    html += `</p>`;
                }
                
                updateResultsPanel(html);
                
                // Highlight the path in the visualization
                highlightPath(data.path);
                
            } else {
                // Show error message
                let html = `<p class="text-danger">Error: ${data.message}</p>`;
                if (data.conflicts) {
                    html += `<p>Conflicts with:</p><ul>`;
                    data.conflicts.forEach(conflict => {
                        html += `<li>${conflict.network} on ${conflict.device}</li>`;
                    });
                    html += `</ul>`;
                }
                updateResultsPanel(html);
            }
            
        } catch (error) {
            console.error('Error performing routing query:', error);
            updateResultsPanel('<p class="text-danger">Error performing routing query. Please try again.</p>');
        }
    };
    
    // Highlight a path in the visualization
    const highlightPath = (path) => {
        setHighlightedPath(path);
        
        // Reset previous highlights
        d3.selectAll('.node-device').classed('node-selected', false);
        d3.selectAll('.link-default').classed('link-active', false);
        
        // Collect nodes and links to highlight
        const deviceIds = new Set();
        const connectionPairs = new Set();
        
        path.forEach((hop, index) => {
            deviceIds.add(hop.device_id);
            
            // If there's a next hop, add the connection
            if (index < path.length - 1 && path[index + 1]) {
                const sourceId = hop.device_id;
                const targetId = path[index + 1].device_id;
                connectionPairs.add(`${sourceId}-${targetId}`);
                connectionPairs.add(`${targetId}-${sourceId}`); // Add both directions
            }
        });
        
        // Highlight nodes
        d3.selectAll('.node-device')
            .filter(d => deviceIds.has(d.id))
            .classed('node-selected', true);
            
        // Highlight links
        d3.selectAll('.link-default')
            .filter(d => {
                return connectionPairs.has(`${d.source.id}-${d.target.id}`) ||
                       connectionPairs.has(`${d.target.id}-${d.source.id}`);
            })
            .classed('link-active', true);
            
        // Check if we should zoom to fit the path
        if (document.getElementById('zoom-on-select').checked) {
            zoomToFitSelection(Array.from(deviceIds));
        }
    };
    
    // Zoom to fit selected nodes
    const zoomToFitSelection = (deviceIds) => {
        if (!svgRef.current || !deviceIds.length) return;
        
        const svg = svgRef.current;
        const width = svg.attr('width');
        const height = svg.attr('height');
        
        // Find nodes to include in the zoom
        const nodesToInclude = topology.nodes.filter(node => deviceIds.includes(node.id));
        
        if (nodesToInclude.length < 2) return; // Not enough nodes to zoom
        
        // Calculate bounds
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        nodesToInclude.forEach(node => {
            minX = Math.min(minX, node.x || 0);
            minY = Math.min(minY, node.y || 0);
            maxX = Math.max(maxX, node.x || 0);
            maxY = Math.max(maxY, node.y || 0);
        });
        
        // Add padding
        const padding = 50;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;
        
        // Calculate scale and translate
        const scale = Math.min(
            width / (maxX - minX),
            height / (maxY - minY)
        ) * 0.9; // Scale down a bit to ensure everything fits
        
        const translate = [
            width / 2 - scale * (minX + maxX) / 2,
            height / 2 - scale * (minY + maxY) / 2
        ];
        
        // Apply zoom transform
        svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity
                .translate(translate[0], translate[1])
                .scale(scale));
    };
    
    // Toggle stub networks
    const toggleStubNetworks = async () => {
        const newValue = !showStubNetworks;
        setShowStubNetworks(newValue);
        
        const btn = document.getElementById('toggle-stub-btn');
        btn.innerText = newValue ? 'Hide Stub Networks' : 'Show All Networks';
        
        // Fetch and update topology
        await fetchTopology(newValue);
    };
    
    // Reset view
    const resetView = () => {
        if (!svgRef.current) return;
        
        // Reset zoom
        svgRef.current.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity);
            
        // Clear selection
        setSelectedItem(null);
        setHighlightedPath(null);
        
        // Reset highlights
        d3.selectAll('.node-device').classed('node-selected', false);
        d3.selectAll('.link-default').classed('link-active', false);
        
        // Clear panels
        updateInfoPanel('<h5>Information Panel</h5><p>Click on a device or connection to see details.</p>');
        updateResultsPanel('<p class="text-muted">No query results yet.</p>');
        
        // Clear form
        document.getElementById('source-input').value = '';
        document.getElementById('destination-input').value = '';
    };
    
    return (
        <div id="topology-visualization">
            {/* D3 will render here */}
        </div>
    );
};

// Helper function to update the info panel
function updateInfoPanel(html) {
    document.getElementById('network-info').innerHTML = html;
}

// Helper function to update the results panel
function updateResultsPanel(html) {
    document.getElementById('results-content').innerHTML = html;
}

// Render the React app
ReactDOM.render(
    <NetworkTopology />,
    document.getElementById('topology-container')
);