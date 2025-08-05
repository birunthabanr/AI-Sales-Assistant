import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";

const Profile = () => {
  const user = {
    name: "John Doe",
    email: "john.doe@example.com",
    joinDate: "January 2024",
    messageCount: 45,
    eventsCreated: 12,
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="max-w-4xl mx-auto p-4">
        <Card>
          <CardHeader>
            <CardTitle>User Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-6 mb-6">
              <Avatar className="h-24 w-24">
                <AvatarImage src="" />
                <AvatarFallback className="text-2xl">
                  {user.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-2xl font-bold">{user.name}</h2>
                <p className="text-muted-foreground">{user.email}</p>
                <p className="text-sm text-muted-foreground">Member since {user.joinDate}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <span>Messages Sent</span>
                <Badge variant="secondary">{user.messageCount}</Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <span>Events Created</span>
                <Badge variant="secondary">{user.eventsCreated}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Profile;