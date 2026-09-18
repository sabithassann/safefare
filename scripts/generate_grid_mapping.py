import json
import os
import argparse

def generate_mapping(
    stops, 
    start_x, 
    start_y, 
    cell_width, 
    cell_height, 
    output_path
):
    mapping = {
        "stops": {},
        "fares": {}
    }

    # Generate dummy stops mapping (assuming stops are on the left of the grid)
    # This is an approximation, the user might need to adjust stop coordinates manually if they are not in a perfect grid next to fares
    for i, stop in enumerate(stops):
        mapping["stops"][stop] = {
            "x": start_x - cell_width, # Assuming stop names are one column to the left
            "y": start_y + i * cell_height,
            "width": cell_width,
            "height": cell_height
        }

    # Generate fare mapping
    # Assuming a full matrix where row = source, col = destination
    for row_idx, source in enumerate(stops):
        for col_idx, dest in enumerate(stops):
            if source == dest:
                continue # No fare to same stop
                
            fare_key = f"{source}_{dest}"
            x = start_x + (col_idx * cell_width)
            y = start_y + (row_idx * cell_height)
            
            # Dummy fare calculation based on distance
            dummy_fare = abs(row_idx - col_idx) * 5.0
            
            mapping["fares"][fare_key] = {
                "amount": dummy_fare,
                "box": {
                    "x": x,
                    "y": y,
                    "width": cell_width,
                    "height": cell_height
                }
            }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4)
        
    print(f"Successfully generated mapping with {len(stops)} stops and {len(mapping['fares'])} fares at {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fare chart coordinate mapping.")
    parser.add_argument("--start-x", type=int, default=100, help="X coordinate of the top-left fare cell")
    parser.add_argument("--start-y", type=int, default=150, help="Y coordinate of the top-left fare cell")
    parser.add_argument("--cell-width", type=int, default=50, help="Width of a single fare cell")
    parser.add_argument("--cell-height", type=int, default=30, help="Height of a single fare cell")
    parser.add_argument("--stops", type=str, default="mirpur_10,kazipara,shewrapara,agargaon,farmgate", help="Comma-separated list of stops")
    parser.add_argument("--output", type=str, default="data/route_mapping.json", help="Output JSON file path")
    
    args = parser.parse_args()
    
    stop_list = [s.strip() for s in args.stops.split(",")]
    
    # Calculate output path relative to project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_abs_path = os.path.join(project_root, args.output)
    
    generate_mapping(
        stops=stop_list,
        start_x=args.start_x,
        start_y=args.start_y,
        cell_width=args.cell_width,
        cell_height=args.cell_height,
        output_path=output_abs_path
    )
