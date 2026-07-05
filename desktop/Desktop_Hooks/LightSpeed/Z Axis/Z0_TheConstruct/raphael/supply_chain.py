"""
Interplanetary Supply Chain Module
Network optimization for Type I Civilization logistics

For: LightSpeed TheConstruct Layer - Römer Industries
"""

import numpy as np
from collections import defaultdict
import json

class SupplyChainNetwork:
    """
    Interplanetary supply chain network simulator

    Manages nodes (sources, processing, destinations) and
    routes (transport links with delta-v costs)
    """

    def __init__(self):
        self.nodes = {}
        self.routes = []
        self.inventory = defaultdict(lambda: defaultdict(float))

    def add_node(self, node_id, node_type, location, capacity_tons):
        """Add a supply chain node"""
        self.nodes[node_id] = {
            'type': node_type,  # source, processing, destination, relay
            'location': location,
            'capacity_tons': capacity_tons,
            'current_inventory': 0
        }

    def add_route(self, source_id, dest_id, transport_type, delta_v, time_days, cost_per_ton, capacity_tons):
        """Add a transport route between nodes"""
        self.routes.append({
            'source': source_id,
            'destination': dest_id,
            'transport': transport_type,
            'delta_v_ms': delta_v,
            'time_days': time_days,
            'cost_per_ton': cost_per_ton,
            'capacity_tons': capacity_tons
        })

    def find_route(self, source_id, dest_id):
        """Find route between two nodes"""
        for route in self.routes:
            if route['source'] == source_id and route['destination'] == dest_id:
                return route
        return None

    def calculate_delivery_cost(self, source_id, dest_id, cargo_tons):
        """Calculate cost to deliver cargo between nodes"""
        route = self.find_route(source_id, dest_id)
        if not route:
            return None

        if cargo_tons > route['capacity_tons']:
            # Multiple trips required
            trips = int(np.ceil(cargo_tons / route['capacity_tons']))
            total_cost = trips * route['cost_per_ton'] * route['capacity_tons']
            total_time = trips * route['time_days']
        else:
            total_cost = cargo_tons * route['cost_per_ton']
            total_time = route['time_days']

        return {
            'total_cost_usd': total_cost,
            'total_time_days': total_time,
            'route': route
        }

    def optimize_multi_leg_delivery(self, source_id, dest_id, cargo_tons):
        """
        Find optimal multi-leg path (if direct route doesn't exist)
        Uses Dijkstra's algorithm for shortest path
        """
        # Build adjacency graph
        graph = defaultdict(list)
        for route in self.routes:
            graph[route['source']].append({
                'node': route['destination'],
                'cost': route['cost_per_ton'] * cargo_tons,
                'time': route['time_days']
            })

        # Dijkstra's algorithm
        visited = set()
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[source_id] = 0
        parent = {}
        path = []

        while len(visited) < len(self.nodes):
            # Find unvisited node with minimum distance
            min_dist = float('inf')
            min_node = None
            for node_id in self.nodes:
                if node_id not in visited and distances[node_id] < min_dist:
                    min_dist = distances[node_id]
                    min_node = node_id

            if min_node is None:
                break

            visited.add(min_node)

            # Update distances to neighbors
            for neighbor in graph[min_node]:
                new_dist = distances[min_node] + neighbor['cost']
                if new_dist < distances[neighbor['node']]:
                    distances[neighbor['node']] = new_dist
                    parent[neighbor['node']] = min_node

        # Reconstruct path
        if dest_id in parent:
            current = dest_id
            while current != source_id:
                path.insert(0, current)
                current = parent[current]
            path.insert(0, source_id)

        return {
            'path': path,
            'total_cost': distances[dest_id],
            'legs': len(path) - 1
        }

    def simulate_mission(self, mission_plan):
        """
        Simulate complete mission logistics

        mission_plan format:
        {
            'legs': [
                {'source': 'earth_leo', 'dest': 'asteroid_belt', 'cargo_tons': 50},
                {'source': 'asteroid_belt', 'dest': 'mars', 'cargo_tons': 100},
            ]
        }
        """
        total_cost = 0
        total_time = 0
        leg_details = []

        for i, leg in enumerate(mission_plan['legs']):
            delivery = self.calculate_delivery_cost(
                leg['source'],
                leg['dest'],
                leg['cargo_tons']
            )

            if delivery:
                total_cost += delivery['total_cost_usd']
                total_time += delivery['total_time_days']

                leg_details.append({
                    'leg': i + 1,
                    'source': leg['source'],
                    'destination': leg['dest'],
                    'cargo_tons': leg['cargo_tons'],
                    'cost_usd': delivery['total_cost_usd'],
                    'time_days': delivery['total_time_days'],
                    'transport': delivery['route']['transport']
                })

        return {
            'legs': leg_details,
            'total_cost_usd': total_cost,
            'total_time_days': total_time,
            'total_cargo_tons': sum(leg['cargo_tons'] for leg in mission_plan['legs'])
        }

    def to_dict(self):
        """Export network to dictionary"""
        return {
            'nodes': self.nodes,
            'routes': self.routes
        }

    def to_json(self, filename=None):
        """Export network to JSON"""
        data = self.to_dict()
        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

def create_romer_supply_chain():
    """
    Create Römer Industries standard supply chain network
    """
    network = SupplyChainNetwork()

    # Add nodes
    network.add_node('earth_surface', 'source', 'Earth_Surface', 1000000)
    network.add_node('earth_leo', 'relay', 'LEO_Station', 50000)
    network.add_node('earth_geo', 'relay', 'GEO_Platform', 10000)
    network.add_node('lunar_surface', 'source', 'Lunar_Base', 5000)
    network.add_node('asteroid_belt', 'source', 'Asteroid_Main_Belt', 100000000)
    network.add_node('orbital_refinery', 'processing', 'GEO_Refinery', 10000)
    network.add_node('deep_space_depot', 'relay', 'L1_Depot', 20000)
    network.add_node('mars_orbit', 'relay', 'Mars_Orbit_Station', 5000)
    network.add_node('mars_surface', 'destination', 'Mars_Colony', 2000)

    # Add routes (source, dest, transport, delta_v, time_days, cost_per_ton, capacity_tons)
    network.add_route('earth_surface', 'earth_leo', 'Luke_II', 9400, 0.5, 1000, 50)
    network.add_route('earth_leo', 'earth_geo', 'Luke_III', 4500, 7, 5000, 20)
    network.add_route('earth_leo', 'lunar_surface', 'Luke_II', 6000, 3, 3000, 50)
    network.add_route('earth_geo', 'orbital_refinery', 'Transfer', 100, 1, 500, 100)
    network.add_route('earth_leo', 'asteroid_belt', 'Mark_III', 6000, 180, 50000, 100)
    network.add_route('asteroid_belt', 'orbital_refinery', 'Mark_V', 4000, 200, 40000, 200)
    network.add_route('orbital_refinery', 'deep_space_depot', 'Luke_IV', 2000, 30, 10000, 50)
    network.add_route('deep_space_depot', 'mars_orbit', 'Luke_IV', 5700, 260, 75000, 15)
    network.add_route('mars_orbit', 'mars_surface', 'Luke_II', 4100, 1, 2000, 30)

    return network

if __name__ == '__main__':
    print("=== Supply Chain Module Test ===\n")

    # Create Römer Industries supply chain
    network = create_romer_supply_chain()
    print(f"Created network with {len(network.nodes)} nodes and {len(network.routes)} routes\n")

    # Test simple delivery
    print("=== LEO to Asteroid Delivery ===")
    delivery = network.calculate_delivery_cost('earth_leo', 'asteroid_belt', 50)
    if delivery:
        print(f"  Cargo: 50 tons")
        print(f"  Cost: ${delivery['total_cost_usd']:,.2f}")
        print(f"  Time: {delivery['total_time_days']:.1f} days")
        print(f"  Transport: {delivery['route']['transport']}")

    # Test mission simulation
    print("\n=== Mission 1: Mining and Return ===")
    mission = {
        'legs': [
            {'source': 'earth_surface', 'dest': 'earth_leo', 'cargo_tons': 50},  # Launch supplies
            {'source': 'earth_leo', 'dest': 'asteroid_belt', 'cargo_tons': 50},  # To asteroid
            {'source': 'asteroid_belt', 'dest': 'orbital_refinery', 'cargo_tons': 150},  # Return ore
            {'source': 'orbital_refinery', 'dest': 'earth_geo', 'cargo_tons': 100},  # Refined materials
        ]
    }

    result = network.simulate_mission(mission)
    print(f"  Total legs: {len(result['legs'])}")
    print(f"  Total cost: ${result['total_cost_usd']:,.2f}")
    print(f"  Total time: {result['total_time_days']:.1f} days ({result['total_time_days']/365:.2f} years)")
    print(f"  Total cargo moved: {result['total_cargo_tons']} tons")
    print("\n  Leg breakdown:")
    for leg in result['legs']:
        print(f"    {leg['leg']}. {leg['source']} → {leg['destination']}: {leg['cargo_tons']} tons via {leg['transport']} (${leg['cost_usd']:,.0f}, {leg['time_days']:.0f} days)")

    # Export network
    print("\n=== Network Export ===")
    print("Exporting to JSON...")
    json_data = network.to_json('supply_chain_network.json')
    print("Network exported successfully!")

    print("\nSupply chain module ready!")
