import React from 'react';
import Link from 'next/link';
import { 
  Shield, ArrowRight, Users, MessageSquare, Activity, Lock, Globe, Zap, 
  Smartphone, Database, Eye, Settings, Cpu, Network, BookOpen, AlertTriangle,
  CheckCircle, Clock, UserCheck
} from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <nav className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Shield className="w-8 h-8 text-emerald-400" />
              <span className="font-bold text-white text-xl">SainyaSecure</span>
            </div>
            <div className="flex items-center gap-4">
              <Link 
                href="/login" 
                className="text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Login
              </Link>
              <Link 
                href="/dashboard" 
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] px-4">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo */}
          <div className="inline-flex items-center justify-center w-24 h-24 bg-emerald-600 rounded-full mb-8 shadow-2xl">
            <Shield className="w-12 h-12 text-white" />
          </div>
          
          {/* Title */}
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
            SainyaSecure
          </h1>
          
          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-slate-300 mb-6">
            Military Communication System
          </p>
          <p className="text-lg text-slate-400 mb-12 max-w-2xl mx-auto">
            Secure, encrypted, and reliable communication platform designed for military operations with advanced security protocols
          </p>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link href="/login">
              <button className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-4 px-8 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center gap-3 mx-auto">
                <Shield className="w-5 h-5" />
                Access Secure Portal
                <ArrowRight className="w-5 h-5" />
              </button>
            </Link>
            
            <Link href="/dashboard">
              <button className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-4 px-8 rounded-lg transition-colors flex items-center gap-3 mx-auto">
                <Activity className="w-5 h-5" />
                View Dashboard
              </button>
            </Link>
          </div>
          
          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700 rounded-lg p-6 text-center hover:bg-slate-800/50 transition-all">
              <div className="w-12 h-12 bg-blue-600 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Secure Communication</h3>
              <p className="text-slate-400">End-to-end encryption with military-grade security protocols</p>
            </div>
            
            <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700 rounded-lg p-6 text-center hover:bg-slate-800/50 transition-all">
              <div className="w-12 h-12 bg-green-600 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Real-time Messaging</h3>
              <p className="text-slate-400">Instant synchronization across all authorized devices</p>
            </div>
            
            <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700 rounded-lg p-6 text-center hover:bg-slate-800/50 transition-all">
              <div className="w-12 h-12 bg-purple-600 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Clearance Control</h3>
              <p className="text-slate-400">Role-based access with military clearance levels</p>
            </div>
          </div>

          {/* Advanced Features Section */}
          <div className="bg-slate-800/20 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 mb-16">
            <h2 className="text-3xl font-bold text-white text-center mb-2">Advanced Military Features</h2>
            <p className="text-slate-400 text-center mb-12 max-w-3xl mx-auto">
              Comprehensive security and communication suite designed for modern military operations
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Device Joining System */}
              <div className="bg-gradient-to-br from-emerald-600/20 to-emerald-800/20 border border-emerald-500/30 rounded-lg p-6 hover:border-emerald-400/50 transition-all">
                <div className="w-10 h-10 bg-emerald-600 rounded-lg mb-4 flex items-center justify-center">
                  <Smartphone className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-emerald-300 font-semibold mb-2">Device Joining</h3>
                <p className="text-slate-400 text-sm mb-3">Authority-approved device registration with secure joining links</p>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 text-xs">Active</span>
                </div>
              </div>

              {/* Blockchain Integration */}
              <div className="bg-gradient-to-br from-blue-600/20 to-blue-800/20 border border-blue-500/30 rounded-lg p-6 hover:border-blue-400/50 transition-all">
                <div className="w-10 h-10 bg-blue-600 rounded-lg mb-4 flex items-center justify-center">
                  <Database className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-blue-300 font-semibold mb-2">Blockchain Ledger</h3>
                <p className="text-slate-400 text-sm mb-3">Immutable transaction logging and secure data integrity</p>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-yellow-400" />
                  <span className="text-yellow-400 text-xs">In Development</span>
                </div>
              </div>

              {/* AI Anomaly Detection */}
              <div className="bg-gradient-to-br from-purple-600/20 to-purple-800/20 border border-purple-500/30 rounded-lg p-6 hover:border-purple-400/50 transition-all">
                <div className="w-10 h-10 bg-purple-600 rounded-lg mb-4 flex items-center justify-center">
                  <Eye className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-purple-300 font-semibold mb-2">AI Security Monitor</h3>
                <p className="text-slate-400 text-sm mb-3">Intelligent threat detection and anomaly analysis</p>
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-purple-400" />
                  <span className="text-purple-400 text-xs">AI Powered</span>
                </div>
              </div>

              {/* P2P Sync */}
              <div className="bg-gradient-to-br from-orange-600/20 to-orange-800/20 border border-orange-500/30 rounded-lg p-6 hover:border-orange-400/50 transition-all">
                <div className="w-10 h-10 bg-orange-600 rounded-lg mb-4 flex items-center justify-center">
                  <Network className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-orange-300 font-semibold mb-2">P2P Sync</h3>
                <p className="text-slate-400 text-sm mb-3">Peer-to-peer data synchronization across secure networks</p>
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-orange-400" />
                  <span className="text-orange-400 text-xs">Real-time</span>
                </div>
              </div>
            </div>

            {/* Authority Dashboard Preview */}
            <div className="mt-12 bg-slate-800/40 border border-slate-600/50 rounded-xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <UserCheck className="w-8 h-8 text-emerald-400" />
                <h3 className="text-2xl font-bold text-white">Authority Dashboard</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-emerald-400 mb-2">156</div>
                  <p className="text-slate-400">Active Devices</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-400 mb-2">23</div>
                  <p className="text-slate-400">Pending Approvals</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-400 mb-2">99.8%</div>
                  <p className="text-slate-400">Security Score</p>
                </div>
              </div>

              <div className="mt-6 flex justify-center">
                <Link href="/dashboard">
                  <button className="bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-700 hover:to-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    Access Authority Panel
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Security Notice */}
          <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-8">
            <div className="flex items-center justify-center gap-2">
              <Shield className="w-5 h-5 text-amber-400" />
              <p className="text-amber-200 font-medium">CLASSIFIED SYSTEM - FOR AUTHORIZED PERSONNEL ONLY</p>
            </div>
            <p className="text-amber-300/80 text-sm mt-1">All activities are monitored and logged for security purposes</p>
          </div>
          
          {/* Footer */}
          <div className="text-center text-slate-500 text-sm">
            <p>© 2025 SainyaSecure Military Communication System</p>
            <p className="mt-1">Developed for secure military communications</p>
          </div>
        </div>
      </div>
    </div>
  );
}
