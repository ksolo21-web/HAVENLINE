import json
p=json.load(open('result.json'))
out={'status':p['status'],'exact_source_material_geometry':p['source_exact_hashes'],
     'max_GLTF_to_native_triangle_position_component_delta_m':max(m['max_abs_component_error_m'] for m in p['decoded_glb_to_native_triangle_bijection']),
     'matched_source_triangle_count':sum(x['position_triangle_count'] for x in p['decoded_glb_to_native_triangle_bijection']),
     'current_stock_payment_unchanged':p['existing_stock_payment_unchanged'],'sides':{}}
for side,q in p['proposed_unbound_two_sided_patches'].items():
    poses=q['exact_axial_and_sideways_pivot_probes'];pose0=poses[f'temp-{side}-+0']['origins']
    hands=[o for v in poses.values() for name,o in v['origins'].items() if name in ('L_Hand','R_Hand')]
    heads=[v['origins']['Head'] for v in poses.values()]
    paths=[o['concept_only_lift_then_level_hover'] for o in hands]
    support=q['footprint']
    out['sides'][side]=dict(actual_board_rest=q['actual_rest'],allowed_role='unbound_geometry_feasibility_only',
     hover=q['point_50mm_above'],covered_square_fraction=support['coverage_fraction'],
     exact_clipped_top_height_span_m=support['exact_clipped_height_span_m'],
     facets_inside_diagnostic_air_box=support['box_from_top_max_plus_1mm_to_50mm_hover_unchanged_donor_contained_facet_count'],
     actual_head_to_rest_clear_counts=[sum(v['direct_to_actual_rest']['no_early_hit'] for v in heads),len(heads)],
     actual_head_to_50mm_hover_clear_counts=[sum(v['direct_to_hypothetical_50mm_hover']['no_early_hit'] for v in heads),len(heads)],
     actual_hand_to_rest_clear_counts=[sum(v['direct_to_actual_rest']['no_early_hit'] for v in hands),len(hands)],
     actual_hand_to_50mm_hover_clear_counts=[sum(v['direct_to_hypothetical_50mm_hover']['no_early_hit'] for v in hands),len(hands)],
     axial_direct_hover={k:v['direct_to_hypothetical_50mm_hover'] for k,v in pose0.items()},
     min_centerline_clearance_for_diagnostic_lift_then_level_m=min(v['combined_minimum_centerline_to_donor_surface_distance_m'] for v in paths),
     best_axial_lift_then_level_centerline_path_length_m=min(v['concept_only_lift_then_level_hover']['combined_path_length_m'] for k,v in pose0.items() if k!='Head'),
     best_all_tested_lift_then_level_centerline_path_length_m=min(v['combined_path_length_m'] for v in paths),
     final_vertical_center_descent=q['hover_to_rest_zero_radius_descent'])
print(json.dumps(out,indent=2,sort_keys=True))
