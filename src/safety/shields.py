def safety_shield(current_pos, proposed_action, min_sep=5.0):
    # Predict next position
    next_pos = current_pos + proposed_action
    
    # Conflict Detection: If next_pos violates distance
    if detect_collision(next_pos):
        return get_corrective_action(current_pos)
    
    return proposed_action
