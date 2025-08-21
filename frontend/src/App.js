import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
import { Separator } from "./components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Heart, MessageCircle, Plus, User, Settings, Car, Users, Calendar, DollarSign, MapPin, Clock, UserPlus, UserMinus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
      setToken(null);
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/login`, userData);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setToken(token);
      setUser(user);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setToken(token);
      setUser(user);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Components
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-amber-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-2">
            <Car className="h-8 w-8 text-amber-600" />
            <h1 className="text-2xl font-bold text-gray-900">AutoSocial Hub</h1>
          </div>
          
          {user && (
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                <Users className="h-4 w-4 mr-2" />
                Following: {user.followed_users?.length || 0}
              </Button>
              <Avatar className="h-8 w-8">
                <AvatarImage src={user.profile_image} />
                <AvatarFallback className="bg-amber-100 text-amber-700">
                  {user.username?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-gray-700">@{user.username}</span>
              <Button variant="outline" size="sm" onClick={logout}>
                Logout
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    bio: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin ? await login(formData) : await register(formData);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center px-4">
      <Card className="w-full max-w-md shadow-xl border-0 bg-white/90 backdrop-blur-sm">
        <CardHeader className="text-center pb-2">
          <div className="flex justify-center mb-4">
            <Car className="h-12 w-12 text-amber-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">AutoSocial Hub</CardTitle>
          <CardDescription className="text-gray-600">
            {isLogin ? 'Welcome back to the car community' : 'Join the ultimate car projects community'}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
                className="mt-1"
              />
            </div>
            
            {!isLogin && (
              <>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="bio">Bio (Optional)</Label>
                  <Textarea
                    id="bio"
                    value={formData.bio}
                    onChange={(e) => setFormData({...formData, bio: e.target.value})}
                    placeholder="Tell us about your car passion..."
                    className="mt-1"
                    rows={3}
                  />
                </div>
              </>
            )}
            
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md border border-red-200">
                {error}
              </div>
            )}
            
            <Button type="submit" className="w-full bg-amber-600 hover:bg-amber-700" disabled={loading}>
              {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
            </Button>
          </form>
        </CardContent>
        
        <CardFooter className="justify-center">
          <Button
            variant="ghost"
            onClick={() => setIsLogin(!isLogin)}
            className="text-amber-600 hover:text-amber-700"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

const ProjectCard = ({ project, onLike, onComment }) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const response = await axios.get(`${API}/projects/${project.id}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      const response = await axios.post(`${API}/comments`, {
        project_id: project.id,
        content: newComment
      });
      setComments([...comments, response.data]);
      setNewComment('');
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

  const toggleComments = () => {
    if (!showComments) {
      fetchComments();
    }
    setShowComments(!showComments);
  };

  return (
    <Card className="w-full shadow-md hover:shadow-lg transition-shadow border-amber-100">
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-3">
          <Avatar className="h-10 w-10">
            <AvatarImage src={project.user?.profile_image} />
            <AvatarFallback className="bg-amber-100 text-amber-700">
              {project.user?.username?.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold text-gray-900">@{project.user?.username}</h3>
            <p className="text-sm text-gray-500">
              {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{project.title}</h2>
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
            <Badge variant="secondary" className="bg-amber-100 text-amber-800">
              {project.car_year} {project.car_make} {project.car_model}
            </Badge>
            {project.build_cost > 0 && (
              <Badge variant="outline" className="text-green-700 border-green-200">
                <DollarSign className="h-3 w-3 mr-1" />
                ${project.build_cost.toLocaleString()}
              </Badge>
            )}
          </div>
          <p className="text-gray-700 mb-3">{project.description}</p>
          
          {project.modifications && project.modifications.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Modifications:</h4>
              <div className="flex flex-wrap gap-2">
                {project.modifications.map((mod, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {mod}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {project.images && project.images.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {project.images.slice(0, 4).map((image, index) => (
              <img
                key={index}
                src={image}
                alt={`${project.title} ${index + 1}`}
                className="w-full h-48 object-cover rounded-lg border border-gray-200"
              />
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between items-center pt-4 border-t border-gray-100">
        <div className="flex space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onLike(project.id)}
            className="text-gray-600 hover:text-red-600"
          >
            <Heart className="h-4 w-4 mr-1" />
            {project.likes_count || 0}
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleComments}
            className="text-gray-600 hover:text-blue-600"
          >
            <MessageCircle className="h-4 w-4 mr-1" />
            {project.comments_count || 0}
          </Button>
        </div>
      </CardFooter>

      {showComments && (
        <div className="px-6 pb-6 border-t border-gray-100">
          <div className="mt-4 space-y-3">
            {loadingComments ? (
              <p className="text-sm text-gray-500">Loading comments...</p>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} className="flex space-x-2">
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs bg-amber-100 text-amber-700">
                      {comment.username?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="bg-gray-50 rounded-lg px-3 py-2">
                      <p className="text-xs font-medium text-gray-900">@{comment.username}</p>
                      <p className="text-sm text-gray-700">{comment.content}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(comment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <form onSubmit={handleAddComment} className="mt-4 flex space-x-2">
            <Input
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1"
            />
            <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-700">
              Post
            </Button>
          </form>
        </div>
      )}
    </Card>
  );
};

const CreateEventModal = ({ onEventCreated }) => {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_date: '',
    event_time: '',
    location: '',
    event_type: 'car_meet',
    max_participants: '',
    images: ''
  });
  const [loading, setLoading] = useState(false);

  const eventTypes = [
    { value: 'car_meet', label: 'Car Meet' },
    { value: 'car_show', label: 'Car Show' },
    { value: 'race', label: 'Race Event' },
    { value: 'workshop', label: 'Workshop' },
    { value: 'cruise', label: 'Cruise' },
    { value: 'track_day', label: 'Track Day' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const eventData = {
        ...formData,
        max_participants: formData.max_participants ? parseInt(formData.max_participants) : null,
        images: formData.images.split(',').map(img => img.trim()).filter(img => img)
      };

      const response = await axios.post(`${API}/events`, eventData);
      onEventCreated(response.data);
      setOpen(false);
      setFormData({
        title: '',
        description: '',
        event_date: '',
        event_time: '',
        location: '',
        event_type: 'car_meet',
        max_participants: '',
        images: ''
      });
    } catch (error) {
      console.error('Failed to create event:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-amber-600 hover:bg-amber-700">
          <Plus className="h-4 w-4 mr-2" />
          New Event
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Car Event</DialogTitle>
          <DialogDescription>
            Organize a car event for the community
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="title">Event Title</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              required
              placeholder="Saturday Night Car Meet"
            />
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
              placeholder="Join us for an awesome car meet..."
              rows={3}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="event_date">Date</Label>
              <Input
                id="event_date"
                type="date"
                value={formData.event_date}
                onChange={(e) => setFormData({...formData, event_date: e.target.value})}
                required
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <Label htmlFor="event_time">Time</Label>
              <Input
                id="event_time"
                type="time"
                value={formData.event_time}
                onChange={(e) => setFormData({...formData, event_time: e.target.value})}
                required
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              required
              placeholder="Downtown Parking Lot, Main St"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="event_type">Event Type</Label>
              <select
                id="event_type"
                value={formData.event_type}
                onChange={(e) => setFormData({...formData, event_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {eventTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="max_participants">Max Participants (Optional)</Label>
              <Input
                id="max_participants"
                type="number"
                value={formData.max_participants}
                onChange={(e) => setFormData({...formData, max_participants: e.target.value})}
                placeholder="50"
                min="1"
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="images">Image URLs (comma-separated)</Label>
            <Input
              id="images"
              value={formData.images}
              onChange={(e) => setFormData({...formData, images: e.target.value})}
              placeholder="https://example.com/image1.jpg, https://example.com/image2.jpg"
            />
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-amber-600 hover:bg-amber-700">
              {loading ? 'Creating...' : 'Create Event'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const EventCard = ({ event, onJoin, onLeave }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleJoinLeave = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      if (event.user_joined) {
        await axios.delete(`${API}/events/${event.id}/join`);
        onLeave(event.id);
      } else {
        await axios.post(`${API}/events/${event.id}/join`);
        onJoin(event.id);
      }
    } catch (error) {
      console.error('Failed to join/leave event:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeLabel = (type) => {
    const types = {
      'car_meet': 'Car Meet',
      'car_show': 'Car Show',
      'race': 'Race Event',
      'workshop': 'Workshop',
      'cruise': 'Cruise',
      'track_day': 'Track Day'
    };
    return types[type] || type;
  };

  const getEventTypeColor = (type) => {
    const colors = {
      'car_meet': 'bg-blue-100 text-blue-800',
      'car_show': 'bg-purple-100 text-purple-800',
      'race': 'bg-red-100 text-red-800',
      'workshop': 'bg-green-100 text-green-800',
      'cruise': 'bg-orange-100 text-orange-800',
      'track_day': 'bg-yellow-100 text-yellow-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const eventDate = new Date(`${event.event_date}T${event.event_time}`);
  const isEventFull = event.max_participants && event.participants_count >= event.max_participants;

  return (
    <Card className="w-full shadow-md hover:shadow-lg transition-shadow border-amber-100">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={event.user?.profile_image} />
              <AvatarFallback className="bg-amber-100 text-amber-700">
                {event.user?.username?.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h3 className="font-semibold text-gray-900">@{event.user?.username}</h3>
              <p className="text-sm text-gray-500">Event Organizer</p>
            </div>
          </div>
          <Badge className={getEventTypeColor(event.event_type)}>
            {getEventTypeLabel(event.event_type)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{event.title}</h2>
          <p className="text-gray-700 mb-4">{event.description}</p>
          
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Calendar className="h-4 w-4 text-amber-600" />
              <span>{eventDate.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4 text-amber-600" />
              <span>{eventDate.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <MapPin className="h-4 w-4 text-amber-600" />
              <span>{event.location}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Users className="h-4 w-4 text-amber-600" />
              <span>
                {event.participants_count} participants
                {event.max_participants && ` (${event.max_participants} max)`}
              </span>
            </div>
          </div>
        </div>

        {event.images && event.images.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {event.images.slice(0, 4).map((image, index) => (
              <img
                key={index}
                src={image}
                alt={`${event.title} ${index + 1}`}
                className="w-full h-32 object-cover rounded-lg border border-gray-200"
              />
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between items-center pt-4 border-t border-gray-100">
        <div className="text-sm text-gray-500">
          {event.participants_count} going
        </div>
        
        {user && user.id !== event.user_id && (
          <Button
            onClick={handleJoinLeave}
            disabled={loading || (!event.user_joined && isEventFull)}
            className={event.user_joined 
              ? "bg-red-600 hover:bg-red-700" 
              : "bg-green-600 hover:bg-green-700"
            }
            size="sm"
          >
            {loading ? '...' : (
              <>
                {event.user_joined ? (
                  <>
                    <UserMinus className="h-4 w-4 mr-1" />
                    Leave Event
                  </>
                ) : isEventFull ? (
                  'Event Full'
                ) : (
                  <>
                    <UserPlus className="h-4 w-4 mr-1" />
                    Join Event
                  </>
                )}
              </>
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

const CreateProjectModal = ({ onProjectCreated }) => {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    car_make: '',
    car_model: '',
    car_year: new Date().getFullYear(),
    description: '',
    modifications: '',
    images: '',
    build_cost: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const projectData = {
        ...formData,
        modifications: formData.modifications.split(',').map(m => m.trim()).filter(m => m),
        images: formData.images.split(',').map(img => img.trim()).filter(img => img),
        build_cost: parseFloat(formData.build_cost) || 0
      };

      const response = await axios.post(`${API}/projects`, projectData);
      onProjectCreated(response.data);
      setOpen(false);
      setFormData({
        title: '',
        car_make: '',
        car_model: '',
        car_year: new Date().getFullYear(),
        description: '',
        modifications: '',
        images: '',
        build_cost: ''
      });
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-amber-600 hover:bg-amber-700">
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Car Project</DialogTitle>
          <DialogDescription>
            Share your latest car build with the community
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="title">Project Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
                placeholder="My Drift Build"
              />
            </div>
            <div>
              <Label htmlFor="car_year">Year</Label>
              <Input
                id="car_year"
                type="number"
                value={formData.car_year}
                onChange={(e) => setFormData({...formData, car_year: parseInt(e.target.value)})}
                required
                min="1900"
                max={new Date().getFullYear() + 1}
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="car_make">Make</Label>
              <Input
                id="car_make"
                value={formData.car_make}
                onChange={(e) => setFormData({...formData, car_make: e.target.value})}
                required
                placeholder="Toyota"
              />
            </div>
            <div>
              <Label htmlFor="car_model">Model</Label>
              <Input
                id="car_model"
                value={formData.car_model}
                onChange={(e) => setFormData({...formData, car_model: e.target.value})}
                required
                placeholder="AE86"
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
              placeholder="Tell us about your project..."
              rows={3}
            />
          </div>
          
          <div>
            <Label htmlFor="modifications">Modifications (comma-separated)</Label>
            <Input
              id="modifications"
              value={formData.modifications}
              onChange={(e) => setFormData({...formData, modifications: e.target.value})}
              placeholder="Coilovers, Turbo kit, Roll cage"
            />
          </div>
          
          <div>
            <Label htmlFor="images">Image URLs (comma-separated)</Label>
            <Input
              id="images"
              value={formData.images}
              onChange={(e) => setFormData({...formData, images: e.target.value})}
              placeholder="https://example.com/image1.jpg, https://example.com/image2.jpg"
            />
          </div>
          
          <div>
            <Label htmlFor="build_cost">Build Cost (USD)</Label>
            <Input
              id="build_cost"
              type="number"
              value={formData.build_cost}
              onChange={(e) => setFormData({...formData, build_cost: e.target.value})}
              placeholder="5000"
              min="0"
              step="0.01"
            />
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-amber-600 hover:bg-amber-700">
              {loading ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const HomePage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (projectId) => {
    try {
      const response = await axios.post(`${API}/likes`, { project_id: projectId });
      // Update the project's like count in the local state
      setProjects(projects.map(project => 
        project.id === projectId 
          ? { ...project, likes_count: response.data.liked ? (project.likes_count || 0) + 1 : (project.likes_count || 1) - 1 }
          : project
      ));
    } catch (error) {
      console.error('Failed to toggle like:', error);
    }
  };

  const handleProjectCreated = (newProject) => {
    // Add user data to the new project
    newProject.user = { 
      id: user.id, 
      username: user.username, 
      profile_image: user.profile_image 
    };
    setProjects([newProject, ...projects]);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="text-center">
          <Car className="h-8 w-8 animate-pulse text-amber-600 mx-auto mb-2" />
          <p className="text-gray-500">Loading amazing car projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Car Projects Feed</h1>
          <p className="text-gray-600">Discover amazing builds from the community</p>
        </div>
        {user && <CreateProjectModal onProjectCreated={handleProjectCreated} />}
      </div>

      <div className="space-y-6">
        {projects.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <Car className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
              <p className="text-gray-500 mb-4">Be the first to share your car project with the community!</p>
              {user && <CreateProjectModal onProjectCreated={handleProjectCreated} />}
            </CardContent>
          </Card>
        ) : (
          projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onLike={handleLike}
            />
          ))
        )}
      </div>
    </div>
  );
};

const EventsPage = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API}/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEventCreated = (newEvent) => {
    // Add user data to the new event
    newEvent.user = { 
      id: user.id, 
      username: user.username, 
      profile_image: user.profile_image 
    };
    newEvent.participants_count = 0;
    newEvent.user_joined = false;
    setEvents([newEvent, ...events]);
  };

  const handleJoinEvent = (eventId) => {
    setEvents(events.map(event => 
      event.id === eventId 
        ? { 
            ...event, 
            participants_count: (event.participants_count || 0) + 1,
            user_joined: true
          }
        : event
    ));
  };

  const handleLeaveEvent = (eventId) => {
    setEvents(events.map(event => 
      event.id === eventId 
        ? { 
            ...event, 
            participants_count: Math.max((event.participants_count || 1) - 1, 0),
            user_joined: false
          }
        : event
    ));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="text-center">
          <Calendar className="h-8 w-8 animate-pulse text-amber-600 mx-auto mb-2" />
          <p className="text-gray-500">Loading upcoming events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Car Events</h1>
          <p className="text-gray-600">Join amazing automotive events in your community</p>
        </div>
        {user && <CreateEventModal onEventCreated={handleEventCreated} />}
      </div>

      <div className="space-y-6">
        {events.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No upcoming events</h3>
              <p className="text-gray-500 mb-4">Be the first to organize a car event for the community!</p>
              {user && <CreateEventModal onEventCreated={handleEventCreated} />}
            </CardContent>
          </Card>
        ) : (
          events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              onJoin={handleJoinEvent}
              onLeave={handleLeaveEvent}
            />
          ))
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App min-h-screen bg-gradient-to-br from-amber-50 via-white to-orange-50">
        <BrowserRouter>
          <AuthContent />
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

const AuthContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <Car className="h-12 w-12 animate-pulse text-amber-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading AutoSocial Hub...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
};

export default App;