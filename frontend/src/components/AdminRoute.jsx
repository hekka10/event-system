import { Navigate, Outlet, useLocation } from 'react-router-dom';

import authService from '../services/authService';


function AdminRoute() {
  const location = useLocation();
  const user = authService.getCurrentUser();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!authService.isAdmin(user)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}


export default AdminRoute;
