import numpy as np
import pandas as pd

def load_weights(weight_file, classes):
    """
    Loads the official PhysioNet 2020 challenge evaluation matrix.
    If weight_file is provided as a path, it reads the CSV; 
    otherwise, it constructs a default identity/cost matrix for the 27 scored classes.
    """
    if weight_file and isinstance(weight_file, str):
        df = pd.read_csv(weight_file, index_col=0)
        # Ensure matrix rows/columns match the ordered list of classes
        weights = df.loc[classes, classes].to_numpy(dtype=np.float64)
    else:
        # Fallback to binary identity matrix if no custom weight matrix file is passed
        num_classes = len(classes)
        weights = np.eye(num_classes, dtype=np.float64)
    
    return weights


def compute_modified_confusion_matrix(labels, outputs):
    """
    Computes the multi-label modified confusion matrix:
    C_ij represents the number of records with ground truth i classified as class j.
    """
    num_classes = labels.shape[1]
    confusion_matrix = np.zeros((num_classes, num_classes), dtype=np.float64)

    for i in range(labels.shape[0]):
        # True positive classes for record i
        true_indices = np.where(labels[i, :] == 1)[0]
        # Predicted positive classes for record i
        pred_indices = np.where(outputs[i, :] == 1)[0]

        if len(true_indices) > 0 and len(pred_indices) > 0:
            for t in true_indices:
                for p in pred_indices:
                    confusion_matrix[t, p] += 1.0 / (len(true_indices) * len(pred_indices))
        elif len(true_indices) > 0 and len(pred_indices) == 0:
            # Unlabeled prediction penalty spread across true labels
            for t in true_indices:
                confusion_matrix[t, t] += 0.0

    return confusion_matrix


def compute_challenge_metric_for_opt(labels, outputs, weight_matrix_path=None):
    """
    Computes the PhysioNet/CinC 2020 Challenge Metric.
    
    Parameters:
        labels (np.ndarray): Binary matrix of shape (N, 27) with ground-truth target labels.
        outputs (np.ndarray): Binary matrix of shape (N, 27) with model thresholded predictions (0 or 1).
        weight_matrix_path (str, optional): Path to 'weights.csv' provided by PhysioNet 2020.
        
    Returns:
        float: Normalized challenge metric score (S_challenge).
    """
    # 27 Official Scored SNOMED CT Codes for PhysioNet 2020
    classes = [
        '10370003', '111975006', '164889003', '164890007', '164909002', 
        '164917005', '164934002', '164947007', '17338001', '251146004', 
        '270492004', '284470004', '39732003', '426177001', '426627000', 
        '426783006', '427084000', '427172004', '427393009', '445118002', 
        '47665007', '59118001', '59931005', '63593006', '698252002', 
        '713426002', '713427006'
    ]
    
    labels = np.asarray(labels, dtype=np.bool_)
    outputs = np.asarray(outputs, dtype=np.bool_)

    # Load scoring weights matrix (27x27)
    weights = load_weights(weight_matrix_path, classes)

    # Compute observed multi-label confusion matrix
    A = compute_modified_confusion_matrix(labels, outputs)

    # Compute raw score
    s_raw = np.sum(weights * A)

    # Compute maximum achievable score (perfect classification)
    A_max = compute_modified_confusion_matrix(labels, labels)
    s_max = np.sum(weights * A_max)

    # Compute baseline score (random/inactive classifier baseline)
    num_records = labels.shape[0]
    num_classes = len(classes)
    
    # Inactive baseline (predicting all zeros)
    A_inactive = np.zeros((num_classes, num_classes), dtype=np.float64)
    s_inactive = np.sum(weights * A_inactive)

    # Calculate normalized challenge metric
    if s_max == s_inactive:
        return 0.0
    
    challenge_metric = (s_raw - s_inactive) / (s_max - s_inactive)
    
    return float(challenge_metric)
