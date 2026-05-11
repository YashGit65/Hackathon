from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

def assign_clusters(df, eps=0.5, min_samples=2, time_weight=1.0, gps_weight=7.0):
    if df.empty:
        return []

    features = df[['timestamp', 'lat', 'lon']]
    scaler = StandardScaler()
    normalized_features = scaler.fit_transform(features)

    normalized_features[:, 0] *= time_weight  
    normalized_features[:, 1] *= gps_weight   
    normalized_features[:, 2] *= gps_weight   

    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = dbscan.fit_predict(normalized_features)

    cluster_mappings = []
    for index, cluster_id in enumerate(cluster_labels):
        db_id = df.iloc[index]['id']
        cluster_mappings.append((int(cluster_id), int(db_id)))
        
    return cluster_mappings