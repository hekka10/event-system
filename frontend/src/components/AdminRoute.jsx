import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

function AdminRoute() {
  const location = useLocation();
  const { user, isAdmin, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!isAdmin) {
    return <Navigate to="/" replace state={{ from: location, error: 'admin_only' }} />;
  }

  return <Outlet />;
}

export default AdminRoute;
