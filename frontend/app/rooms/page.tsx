'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Users, LogOut, Plus, Search, Moon, Sun } from 'lucide-react';
import { useUIStore } from '@/lib/stores/uiStore';
import { RoomSkeleton } from '@/components/ui/Skeleton';
import { ToastContainer } from '@/components/ui/Toast';
import api from '@/lib/api/axios-client';
import CreateRoomModal from '@/components/modals/CreateRoomModal';

interface Room {
 id: string;
 name: string;
 slug: string;
 description?: string;
 message_count: number;
 created_by: {
   username: string;
 };
}

export default function RoomsPage() {
 const [rooms, setRooms] = useState<Room[]>([]);
 const [loading, setLoading] = useState(true);
 const [searchQuery, setSearchQuery] = useState('');
 const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
 const { theme, toggleTheme, addNotification } = useUIStore();

 useEffect(() => {
   const token = window.localStorage.getItem('access_token');
   if (!token) {
     window.location.assign('/login');
     return;
   }

   const loadRooms = async () => {
     try {
       const response = await api.get<Room[]>('/api/rooms/');
       setRooms(Array.isArray(response.data) ? response.data : []);
     } catch (err) {
       console.error('Error fetching rooms:', err);
       addNotification({
         type: 'error',
         message: 'Failed to load rooms. Please try again.',
       });
       setRooms([]);
     } finally {
       setLoading(false);
     }
   };

   loadRooms();
 }, [addNotification]);

 const handleLogout = () => {
   localStorage.clear();
   window.location.assign('/login');
 };

 const goToRoom = (slug: string) => {
   window.location.assign(`/chat/${slug}`);
 };

 const handleCreateSuccess = async () => {
   addNotification({
     type: 'success',
     message: 'Room created successfully!',
   });

   // Reload rooms list
   try {
     const response = await api.get<Room[]>('/api/rooms/');
     setRooms(Array.isArray(response.data) ? response.data : []);
   } catch (err) {
     console.error('Error reloading rooms:', err);
   }
 };

 const filteredRooms = rooms.filter(room =>
   room.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
   room.description?.toLowerCase().includes(searchQuery.toLowerCase())
 );

 return (
   <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#0a0a0b]' : 'bg-gray-50'}`}>
     <ToastContainer />
     <header className={`border-b ${theme === 'dark' ? 'border-white/5 bg-[#111113]/95' : 'border-gray-200 bg-white/95'} backdrop-blur-xl sticky top-0 z-50 shadow-sm`}>
       <div className="max-w-7xl mx-auto px-4 py-3.5">
         <div className="flex items-center justify-between">
           <div className="flex items-center gap-3">
             <motion.div
               initial={{ scale: 0, rotate: -180 }}
               animate={{ scale: 1, rotate: 0 }}
               transition={{ type: "spring", stiffness: 200, damping: 15 }}
               className="w-9 h-9 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30"
             >
               <MessageSquare className="w-6 h-6 text-white" />
             </motion.div>
             <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
               RelayDesk
             </h1>
           </div>

           <div className="flex items-center gap-2">
             <motion.button
               whileHover={{ scale: 1.1, rotate: 180 }}
               whileTap={{ scale: 0.9 }}
               onClick={toggleTheme}
               className={`p-2.5 rounded-xl transition-all ${
                 theme === 'dark' ? 'hover:bg-white/5 text-gray-400 hover:text-yellow-400' : 'hover:bg-gray-100 text-gray-600 hover:text-indigo-600'
               }`}
             >
               {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
             </motion.button>

             <motion.button
               whileHover={{ scale: 1.05, x: 3 }}
               whileTap={{ scale: 0.95 }}
               onClick={handleLogout}
               className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all font-medium ${
                 theme === 'dark' ? 'text-gray-400 hover:text-red-400 hover:bg-white/5' : 'text-gray-600 hover:text-red-600 hover:bg-gray-100'
               }`}
             >
               <LogOut className="w-4 h-4" />
               <span className="hidden sm:inline">Logout</span>
             </motion.button>
           </div>
         </div>
       </div>
     </header>

     <main className="max-w-7xl mx-auto px-4 py-8">
       <motion.div
         initial={{ opacity: 0, y: 20 }}
         animate={{ opacity: 1, y: 0 }}
         className="mb-8"
       >
         <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
           <motion.div
             initial={{ opacity: 0, x: -20 }}
             animate={{ opacity: 1, x: 0 }}
           >
             <h2 className="text-4xl font-bold mb-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
               Chat Rooms
             </h2>
             <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
               {filteredRooms.length} {filteredRooms.length === 1 ? 'room' : 'rooms'} available
             </p>
           </motion.div>

           <motion.button
             whileHover={{ scale: 1.05, y: -2 }}
             whileTap={{ scale: 0.95 }}
             initial={{ opacity: 0, x: 20 }}
             animate={{ opacity: 1, x: 0 }}
             onClick={() => setIsCreateModalOpen(true)}
             className="flex items-center gap-2 px-6 py-3 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white rounded-xl font-semibold shadow-lg shadow-purple-500/40 hover:shadow-purple-500/60 transition-all"
           >
             <Plus className="w-5 h-5" />
             Create Room
           </motion.button>
         </div>

         <motion.div
           initial={{ opacity: 0, y: 10 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.1 }}
           className="relative"
         >
           <Search className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 ${
             theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
           }`} />
           <input
             type="text"
             placeholder="Search rooms..."
             value={searchQuery}
             onChange={(e) => setSearchQuery(e.target.value)}
             className={`w-full pl-12 pr-4 py-3.5 rounded-xl border transition-all ${
               theme === 'dark'
                 ? 'bg-[#1a1a1c] border-white/10 text-white placeholder-gray-500 focus:border-purple-500/50'
                 : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400 focus:border-purple-500/50'
             } focus:outline-none focus:ring-2 focus:ring-purple-500/20 shadow-sm`}
           />
         </motion.div>
       </motion.div>

       {loading && (
         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
           {[...Array(6)].map((_, i) => (
             <RoomSkeleton key={i} />
           ))}
         </div>
       )}

       {!loading && filteredRooms.length > 0 && (
         <motion.div
           initial={{ opacity: 0 }}
           animate={{ opacity: 1 }}
           transition={{ duration: 0.3 }}
           className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
         >
           {filteredRooms.map((room, index) => (
             <motion.div
               key={room.id}
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: index * 0.05, type: "spring", stiffness: 300 }}
               whileHover={{ scale: 1.03, y: -6 }}
               onClick={() => goToRoom(room.slug)}
               className={`rounded-2xl p-6 cursor-pointer transition-all border group ${
                 theme === 'dark'
                   ? 'bg-[#1a1a1c]/80 border-white/5 hover:border-purple-500/50 hover:bg-[#1a1a1c] hover:shadow-2xl hover:shadow-purple-500/20'
                   : 'bg-white border-gray-200 hover:border-purple-400 hover:shadow-2xl hover:shadow-purple-400/20'
               }`}
             >
               <div className="flex items-center gap-3 mb-4">
                 <motion.div
                   whileHover={{ rotate: 360, scale: 1.1 }}
                   transition={{ duration: 0.5 }}
                   className="w-14 h-14 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-purple-500/30 ring-2 ring-purple-500/20"
                 >
                   <MessageSquare className="w-7 h-7 text-white" />
                 </motion.div>
                 <div className="min-w-0 flex-1">
                   <h3 className={`text-lg font-bold truncate transition-colors ${
                     theme === 'dark' ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                   }`}>
                     {room.name}
                   </h3>
                   <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                     {room.message_count} messages
                   </p>
                 </div>
               </div>

               {room.description && (
                 <p className={`text-sm mb-4 line-clamp-2 ${
                   theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                 }`}>
                   {room.description}
                 </p>
               )}

               <div className={`flex items-center gap-2 text-sm ${
                 theme === 'dark' ? 'text-gray-500' : 'text-gray-500'
               }`}>
                 <Users className="w-4 h-4 flex-shrink-0" />
                 <span className="truncate">Created by {room.created_by.username}</span>
               </div>
             </motion.div>
           ))}
         </motion.div>
       )}

       {!loading && filteredRooms.length === 0 && (
         <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           className="text-center py-16"
         >
           <div className={`w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center ${
             theme === 'dark' ? 'bg-gray-800' : 'bg-gray-100'
           }`}>
             <MessageSquare className={`w-10 h-10 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
           </div>
           <h3 className={`text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
             {searchQuery ? 'No rooms found' : 'No rooms available yet'}
           </h3>
           <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
             {searchQuery
               ? 'Try adjusting your search query'
               : 'Create your first room to get started'}
           </p>
         </motion.div>
       )}
     </main>

     {/* Create Room Modal */}
     <CreateRoomModal
       isOpen={isCreateModalOpen}
       onClose={() => setIsCreateModalOpen(false)}
       onSuccess={handleCreateSuccess}
       theme={theme}
     />
   </div>
 );
}
